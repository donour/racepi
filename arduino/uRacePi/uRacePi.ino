/**************************************************************************
    Copyright 2020 Donour Sizemore

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
#define GPS_FIX_SPD_ERR
#define GPS_FIX_LAT_ERR
#define NMEAGPS_PARSE_GLL
#define NMEAGPS_PARSE_GSA
#define LAST_SENTENCE_IN_INTERVAL NMEAGPS::NMEA_GLL

#include "racepi_gnss.h"
#include "dl1.h"
#include <string.h>
#include <math.h> // TODO remove me
#include <NMEAGPS.h>
#include "racepi_gnss.h"
#include <ACAN2515.h>
#include "BluetoothSerial.h"

int16_t process_send_can_message(BluetoothSerial *port, CANMessage *frame);

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth Classic is not enabled for this build. 
#endif

#define SERIAL_CONSOLE_BAUDRATE (115200)

#define DEBUG_PORT Serial
#define UBX_PORT   Serial1

static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "evora";
static const uint32_t MCP2515_QUARTZ_FREQUENCY = 8e6;
static const uint32_t CAN_BITRATE = 5e5;

static const byte MCP2515_SCK  = 23;
static const byte MCP2515_MOSI = 22;
static const byte MCP2515_MISO = 14;
static const byte MCP2515_CS   = 32;

static gps_fix fix;

ACAN2515 canbus (MCP2515_CS, SPI, 255); // disabled interrupts
BluetoothSerial SerialBT;
TaskHandle_t gnss_task, Task2;

int16_t setup_mcp2515(ACAN2515 *can, HardwareSerial &debug_port) {

  ACAN2515Settings settings(MCP2515_QUARTZ_FREQUENCY, CAN_BITRATE);

  // TODO: setup incoming filters

  const uint16_t rc = canbus.begin(settings, NULL);
  if (rc != 0) {
    debug_port.printf("(MCP2515) setup errr: %x", rc);
    return rc;
  }
  debug_port.printf("(MCP2515) bit rate: %d", settings.actualBitRate ());
  return 0;
}

// check for any received GPS data and send to clients it exists
// return 0 if data was sent, non zero on failure
int16_t update_gnss() {
  dl1_message_t dl1_message;
  
  while (gps.available(UBX_PORT)) {
    fix = gps.read();

    // Uncomment this to trace GPS data
    //trace_all(DEBUG_PORT, gps, fix);
    if ( ! get_timestamp_message(&dl1_message, millis())) {
      send_dl1_message(&dl1_message, &SerialBT);
    }
    if ( ! get_speed_message(&dl1_message, fix.speed() * 100, fix.spd_err_mmps/10)) {
      send_dl1_message(&dl1_message, &SerialBT);
    }
    if ( ! get_gps_pos_message(&dl1_message, fix.latitudeL(), fix.longitudeL(), fix.lat_err_cm*10)) {
      send_dl1_message(&dl1_message, &SerialBT);
    }
    return 0;
  } 
  return -1;
}

void gnss_process(void *params) {
  while (true) { 
    if( update_gnss() != 0) {
      delay(1);
    }
  }
}

void callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param){
  if(event == ESP_SPP_CLOSE_EVT ){
    ESP.restart();
  }
}
    
void setup() {
  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  SerialBT.register_callback(callback);
  SerialBT.begin(BLUETOOTH_DEVICE_BROADCAST_NAME); 
  SPI.begin(MCP2515_SCK, MCP2515_MISO, MCP2515_MOSI);
  Serial.write(0); Serial.flush();
  Serial1.write(0); Serial1.flush();
  SerialBT.write(0); SerialBT.flush();
  dl1_init();
  
  int16_t mcp_rc = setup_mcp2515(&canbus, Serial); 
  if (mcp_rc != 0) {
    Serial.printf("(MCP2515) setup error!\n");
  } else {
    // TODO setup MCP2515 filters
    Serial.printf("(MCP2515) setup success!\n");    
  }
  int16_t gnss_rc = setup_ublox_gnss(UBX_PORT); 
  if (gnss_rc != 0) {
    // TODO handle gnss setup errors
    Serial.printf("(GNSS) setup error!\n");
  } else {   
    xTaskCreatePinnedToCore(
      gnss_process,
      "gnss_task",
      2048,
      NULL,
      1,
      &gnss_task,
      0);
  }
}

void test_sends() { 
  dl1_message_t dl1_message;

  if ( ! get_timestamp_message(&dl1_message, millis())) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

//  if ( ! get_speed_message(&dl1_message, (millis()/10) % 200, 10)) {
//    send_dl1_message(&dl1_message, &SerialBT);
//  }
//
//  if ( ! get_gps_pos_message(&dl1_message, 41000000, 3400000, 1200)) {
//    send_dl1_message(&dl1_message, &SerialBT);
//  }

  if ( ! get_tps_message(&dl1_message, (millis()/100) % 101)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_rpm_message(&dl1_message,  sin(millis()/3000.0)*4500 + 4500)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }  

  if ( ! get_steering_angle_message(&dl1_message, sin(millis()/3000.0)*200)){
    send_dl1_message(&dl1_message, &SerialBT);
  }  

  if ( ! get_xy_accel_message(&dl1_message, sin(millis()/3000.0)/1.1, cos(millis()/3000.0)/1.1)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }    
}

void loop() {
  canbus.poll(); 

  CANMessage frame;
  int rc = 0;
  if (canbus.available()) {
    canbus.receive(frame);
    process_send_can_message(&SerialBT, &frame);
  } else {
    // Uncomment to generat test data
    test_sends();
    
    delay(5);    
  }
}
