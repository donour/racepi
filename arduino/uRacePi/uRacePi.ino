/**************************************************************************
    Copyright 2020-2023 Donour Sizemore

    This file is part of RacePi

    RacePi is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2.

    RacePi is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
**************************************************************************/

#define USE_SPARKFUN_UBX
//#define USE_UART_NEOGPS
//#define USE_ICM20600

#define USE_ESP32_CAN
//#define USE_ACAN_SPI

#include <string.h>
#include "dl1.h"
#include "BluetoothSerial.h"
#include "tests.h"
#include "icm20600.h"

#ifdef USE_ESP32_CAN
#include <driver/can.h>
#include "esp32_can_processor.h"
int16_t process_send_can_message_esp32(BluetoothSerial *port, can_message_t *frame, float power_w);
#endif

#ifdef USE_ACAN_SPI
#include <ACAN2515.h>
int16_t process_send_can_message(BluetoothSerial *port, CANMessage *frame);
ACAN2515 canbus (MCP2515_CS, SPI, 255); // disabled interrupts
#endif

#ifdef USE_UART_NEOGPS
#define GPS_FIX_SPD_ERR
#define GPS_FIX_LAT_ERR
#define NMEAGPS_PARSE_GLL
#define NMEAGPS_PARSE_GSA
#include "racepi_gnss.h"
#include <NMEAGPS.h>
static gps_fix fix;
#endif

#ifdef  USE_SPARKFUN_UBX
#include <Wire.h>
#include <SparkFun_u-blox_GNSS_Arduino_Library.h>
SFE_UBLOX_GNSS myGNSS;
#define UBX_PORT   Serial1
TaskHandle_t gnss_task, Task2;
#endif

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth Classic is not enabled for this build. 
#endif

#define SERIAL_CONSOLE_BAUDRATE (115200)
#define GPS_MOVEMENT_THRESHOLD (3.0)
#define SHUTDOWN_IDLE_TIME_MILLIS (3.6e6) // 1 hour
#define SPARKFUN_UBX_REFRESH_RATE_HZ (25)
#define GNSS_LED (13)
#define DEBUG_PORT Serial

float calculate_power_from_speed(
  int16_t speed_x1000, 
  int16_t last_speed_x1000,
  uint32_t gps_time_x1000,
  uint32_t last_gps_time_x1000,
  int16_t elevation);

static int16_t last_speed_x1000 = 0;
static uint32_t last_gps_time_x1000 = 0;
static float calc_power_watts = 0.0;

static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "evora";
static const uint32_t CAN_BITRATE = 5e5;

static const byte MCP2515_SCK  = 22;
static const byte MCP2515_MOSI = 32;
static const byte MCP2515_MISO = 14;
static const byte MCP2515_CS   = 15;

static const byte UBX_SDA_PIN = 21;
static const byte UBX_SCL_PIN = 17;

static const byte ESPCAN_RX_PIN = 22;
static const byte ESPCAN_TX_PIN = 23;

static const byte ICM_SDA_PIN = 15;
static const byte ICM_SCL_PIN = 32;

// used to indicate that we have timed out all data
// and should shutdown
volatile long last_data_rx_millis = millis();

TwoWire icm_i2c = TwoWire(1);
ICM20600 icm = ICM20600();
BluetoothSerial SerialBT;

#ifdef USE_ACAN_SPI
static const uint32_t MCP2515_QUARTZ_FREQUENCY = 8e6;
int16_t setup_mcp2515(ACAN2515 *can, HardwareSerial &debug_port) {

  ACAN2515Settings settings(MCP2515_QUARTZ_FREQUENCY, CAN_BITRATE);

  // TODO: setup incoming filters

  const uint16_t rc = canbus.begin(settings, NULL);
  if (rc != 0) {
    debug_port.printf("(MCP2515) setup errr: %x", rc);
    return rc;
  }
  debug_port.printf("(MCP2515) bit rate: %d\n", settings.actualBitRate ());
  return 0;
}
#endif 

void write_gnss_messages(
  uint32_t speed_ms_x100, 
  uint32_t accuracy_ms_x100, 
  int32_t lat_xe7, 
  int32_t long_xe7, 
  int32_t error_xe3,
  int32_t elevation_m_xe3,
  int32_t elevation_m_acc_xe3,
  unint32_t time_HHMMSSsss) {
    dl1_message_t dl1_message;
    can_message_t message;

    if ( ! get_speed_message(&dl1_message, speed_ms_x100, accuracy_ms_x100)) {
      send_dl1_message(&dl1_message, &SerialBT, true);
    }
    if ( ! get_gps_pos_message(&dl1_message, lat_xe7, long_xe7, error_xe3)) {
      send_dl1_message(&dl1_message, &SerialBT, false);
    }
    if ( ! get_gps_altitude_message(&dl1_message, elevation_m_xe3, elevation_m_acc_xe3)) {
      send_dl1_message(&dl1_message, &SerialBT, false);
    }
    
    if (speed_ms_x100 > GPS_MOVEMENT_THRESHOLD*100) {
      last_data_rx_millis = millis();
    }

#ifdef USE_ESP32_CAN
    uint32_t MOTEC_GNSS_CAN_BASE_ID = 0x680
    uint16_t gps_speed_kmh_x01 = speed_ms_x100 / 100 * 3.6;

    message.identifier = MOTEC_GNSS_CAN_BASE_ID;
    message.data32[0] = lat_xe7;
    message.data32[1] = long_xe7;
    message.len = 8
    can_transmit(&message, pdMS_TO_TICKS(50));

    message.identifier = MOTEC_GNSS_CAN_BASE_ID+1;
    message.data32[0] = time_HHMMSSsss;
    message.data16[2] = gps_speed_kmh_x01;
    message.data16[3] = elevation_m_xe3 / 100;
    message.len = 8
    can_transmit(&message, pdMS_TO_TICKS(50));
#endif
}



void sparkfun_gnss_process(
   uint32_t speed_ms_x1000, 
  uint32_t speed_ms_x100,
  uint32_t accuracy_ms_x100,
  int32_t lat_xe7,
  int32_t long_xe7,
  int32_t error_xe3,
  int32_t elevation_m_xe3,
  int32_t elevation_m_acc_xe3,
  int32_t time_of_week) {

  calc_power_watts = calculate_power_from_speed(
    speed_ms_x1000,
    last_speed_x1000,
    time_of_week,
    last_gps_time_x1000,
    elevation_m_xe3);
  last_gps_time_x1000 = time_of_week;
  last_speed_x1000 = speed_ms_x1000;

  write_gnss_messages(
    speed_ms_x100, 
    accuracy_ms_x100, 
    lat_xe7, 
    long_xe7, 
    error_xe3,
    elevation_m_xe3,
    elevation_m_acc_xe3,
    0);    
}

#ifdef USE_SPARKFUN_UBX
void sparkfun_ubx_pvt_callback(UBX_NAV_PVT_data_t pvt) {
  uint32_t speed_ms_x1000 = pvt.gSpeed; 
  uint32_t speed_ms_x100 = pvt.gSpeed / 10; 
  uint32_t accuracy_ms_x100 = pvt.sAcc/ 10;
  int32_t lat_xe7 = pvt.lat;
  int32_t long_xe7 = pvt.lon;
  int32_t error_xe3 = pvt.hAcc;
  int32_t elevation_m_xe3 = pvt.hMSL;
  int32_t elevation_m_acc_xe3 = pvt.vAcc;
  int32_t time_of_week = pvt.iTOW;

  write_gnss_messages(
    speed_ms_x100, 
    accuracy_ms_x100, 
    lat_xe7, 
    long_xe7, 
    error_xe3,
    elevation_m_xe3,
    elevation_m_acc_xe3,
    0);    
}
#endif //USE_SPARKFUN_UBX

#ifdef USE_UART_NEOGPS
// check for any received GPS data and send to clients it exists
// return 0 if data was sent, non zero on failure
bool gnss_rx_status = false;
int16_t update_gnss() {
  dl1_message_t dl1_message;
  while (gps.available(UBX_PORT)) {
    fix = gps.read();
    float speed_ms_x100 = fix.speed_metersps() * 100;
    write_gnss_messages(
      speed_ms_x100, 
      fix.spd_err_mmps/10, 
      fix.latitudeL(), 
      fix.longitudeL(), 
      fix.lat_err_cm*10,
      0,
      1000,
      0); 
    return 0;
  } 
  return -1;
}

void gnss_process(void *params) {
  while (true) { 
    if( update_gnss() != 0) {
      delayMicroseconds(100);
    }
  }
}
#endif

void bt_callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param){
  if(event == ESP_SPP_CLOSE_EVT ){
    // This is a little heavy handed, but I've had trouble
    // initiating subsequent connections after SPP close, so
    // I just reboot the module.
    ESP.restart();
  }
}

void setup() {    
  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  Serial.write(0); Serial.flush();
  Serial.print("***uRacePi***\n");
  
  SerialBT.register_callback(bt_callback);
  SerialBT.begin(BLUETOOTH_DEVICE_BROADCAST_NAME); 
  SerialBT.write(0); SerialBT.flush();
  Serial.print("Bluetooth setup success!");
  
  pinMode(GNSS_LED, OUTPUT);
  digitalWrite(GNSS_LED, LOW);
  if (dl1_init() !=0) {
    Serial.printf("(DL1 writer setup error!\n");
  } else {
    Serial.printf("DL1 writer setup success!\n");
  }

#ifdef USE_ICM20600
  icm_i2c.begin(ICM_SDA_PIN, ICM_SCL_PIN);
  if (icm.init(&icm_i2c)) {
    Serial.printf("(ICM20600) setup error!\n");
  } {
    Serial.printf("(ICM20600) setup success!\n");    
  }
#endif //USE_ICM20600

#ifdef USE_ACAN_SPI
  SPI.begin(MCP2515_SCK, MCP2515_MISO, MCP2515_MOSI);
  int16_t mcp_rc = setup_mcp2515(&canbus, Serial); 
  if (mcp_rc != 0) {
    Serial.printf("(MCP2515) setup error!\n");
  } else {
    // TODO setup MCP2515 filters
    Serial.printf("(MCP2515) setup success!\n");    
  }
#endif 

#ifdef USE_ESP32_CAN
  int16_t espcan_rc = setup_can_driver(ESPCAN_TX_PIN, ESPCAN_RX_PIN);
  switch (espcan_rc) {
     case 0:
      Serial.printf("(CAN) success!\n");    
      break;
    case -1:
      Serial.printf("(CAN) install failure!\n");        
      break;
    case -2:
      Serial.printf("(CAN) setup failure!\n");        
      break;
    default:
      Serial.printf("(CAN) unknown failure: %d\n", espcan_rc);        
  }
#endif

#ifdef  USE_SPARKFUN_UBX
  Wire.begin(UBX_SDA_PIN, UBX_SCL_PIN);
  if (myGNSS.begin()) {

    // Optional library debugging, printed to Serial(1)
    //myGNSS.enableDebugging()

    myGNSS.setDynamicModel(DYN_MODEL_AUTOMOTIVE);
    
    // Disable non-UBX to save bandwidth and reduce latency on the i2c 
    // link. RTCM is not that expensive, but NMEA is verbose.
    myGNSS.setI2COutput(COM_TYPE_UBX);
    
    myGNSS.setNavigationFrequency(SPARKFUN_UBX_REFRESH_RATE_HZ); 
    myGNSS.setAutoPVT(true);
    // This will optionally persist the settings to NVM on the 
    // GNSS device. 
    //myGNSS.saveConfigSelective(VAL_CFG_SUBSEC_IOPORT);
    //myGNSS.setAutoPVTcallback(&sparkfun_ubx_pvt_callback);
    xTaskCreate(
      sparkfun_ubx_task,
      "GNSSTask",
      2048,
      NULL,
      2,            
      NULL);
    Serial.printf("(GNSS) setup success!\n");
  } else {
    Serial.printf("(GNSS) setup error!\n");    
  }
#endif


//#ifdef USE_UART_NEOGPS
////  Serial1.write(0); Serial1.flush();
////  int16_t gnss_rc = setup_ublox_gnss(UBX_PORT); 
////  if (gnss_rc != 0) {
////    // TODO handle gnss setup errors
////    Serial.printf("(GNSS) setup error!\n");
////  } else {   
////    xTaskCreatePinnedToCore(
////      gnss_process,
////      "gnss_task",
////      2048,
////      NULL,
////      1,
////      &gnss_task,
////      tskNO_AFFINITY);
////     pinMode(LED_BUILTIN, OUTPUT);
////     Serial.printf("(GNSS) setup success!\n");
////    digitalWrite(GNSS_LED, HIGH);
////  }
//#endif
  
}

void check_shutdown_timer() {
  // TODO: this logic is untested
  // TODO: would also need to be wired up to control power on accessories in order to be effective
    if ((millis() - last_data_rx_millis) > SHUTDOWN_IDLE_TIME_MILLIS) {
      Serial.printf("Powering off...\n"); 
#ifdef  USE_SPARKFUN_UBX
      myGNSS.powerOff(0x0FFFFFFF, 0xEFFF);
#endif
      esp_deep_sleep_start();
    }  
}

#ifdef  USE_SPARKFUN_UBX
void sparkfun_ubx_task(void *arg) {
  while (true) {
    if (myGNSS.getPVT() && (myGNSS.getInvalidLlh() == false))
    {
      uint32_t speed_ms_x1000 = myGNSS.getGroundSpeed();
      uint32_t speed_ms_x100 = speed_ms_x1000/10;
      int32_t error_xe3 = myGNSS.getHorizontalAccEst();
      uint32_t accuracy_ms_x100 = error_xe3/10.0;
      int32_t lat_xe7 = myGNSS.getLatitude();
      int32_t long_xe7 = myGNSS.getLongitude();
      int32_t elevation_m_xe3 = myGNSS.getAltitudeMSL();
      int32_t elevation_m_acc_xe3 = myGNSS.getVerticalAccEst();
      int32_t time_of_week = myGNSS.getTimeOfWeek();
  
      //Serial.printf("%d:  %d, %d\n", time_of_week, lat_xe7, long_xe7);
          
      sparkfun_gnss_process(
        speed_ms_x1000, 
        speed_ms_x100,
        accuracy_ms_x100,
        lat_xe7,
        long_xe7,
        error_xe3,
        elevation_m_xe3,
        elevation_m_acc_xe3,
        time_of_week);
    } else {
      delay(1);
    }
    
  }
}
#endif  

void loop() {
#ifdef USE_ESP32_CAN
  can_message_t msg;
  if (can_receive(&msg, pdMS_TO_TICKS(1)) == ESP_OK) {
    process_send_can_message_esp32(&SerialBT, &msg, calc_power_watts);
    //Serial.printf("Canmesg: %d(hz)\n", 1000/((millis()+1) - last_data_rx_millis));
    last_data_rx_millis = millis();
  } else {
    check_shutdown_timer();
    delay(20);
  }
#endif

#ifdef USE_ACAN_SPI
  canbus.poll(); 
  CANMessage frame;
  int rc = 0;
  if (canbus.available()) {
    canbus.receive(frame);
    process_send_can_message(&SerialBT, &frame);
    last_data_rx_millis = millis();
  } else {
    // Uncomment to generat test data
    //test_sends(&SerialBT);
    check_shutdown_timer();
    delay(1);
  }
#endif USE_ACAN_SPI
}
