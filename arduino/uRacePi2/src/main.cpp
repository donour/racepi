/**************************************************************************
    Copyright 2025 Donour Sizemore

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
#include <Arduino.h>
#include <Wire.h>
#include <SparkFun_u-blox_GNSS_Arduino_Library.h>
#include "esp32_can_processor.h"
#include "spp_serial.h"
#include "rc_podium_protocol.h"
#include <driver/twai.h>
#include "esp32_can_processor.h"
#include "esp_freertos_hooks.h"


#define MS_TO_MPH (2.23694f)
#define RED_LED_PIN (13) 

// used to indicate that we have timed out all data
// and should shutdown
volatile long last_data_rx_millis = millis();
#define SHUTDOWN_IDLE_TIME_MILLIS (3.6e6) // 1 hour

#define SERIAL_CONSOLE_BAUDRATE (115200)
#define DEBUG_PORT Serial

#define SPARKFUN_UBX_REFRESH_RATE_HZ (25)
SFE_UBLOX_GNSS myGNSS;
TaskHandle_t gnss_task, Task2;

static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "rp_%02X-%02X-%02X";

static const byte UBX_SDA_PIN = 21;
static const byte UBX_SCL_PIN = 17;

bool date_set = false;

void sparkfun_ubx_task(void *arg) {
  while (true) {
    if (myGNSS.getPVT() && (myGNSS.getInvalidLlh() == false)) {
      float speed_ms = myGNSS.getGroundSpeed() / (float)1e3;
      float  gnss_error = myGNSS.getHorizontalAccEst() / (float)1e3;
      float lat = myGNSS.getLatitude() / (float)1e7;
      float longitude = myGNSS.getLongitude() / (float)1e7;
      float elevation_m = myGNSS.getAltitudeMSL() / (float)1e3;
      float n_sats = myGNSS.getSIV();
      float pdop = myGNSS.getPDOP() / (float)1e2;

      if ( ! date_set && myGNSS.getTimeValid() ) {
        struct timeval tv = {
          .tv_sec = (time_t)myGNSS.getUnixEpoch(),
          .tv_usec = myGNSS.getMillisecond()
        };        
        // print tv as 8601 string
        char buf[64];
        strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", gmtime(&tv.tv_sec));
        Serial.printf("Setting system time to GNSS time: %s\n", buf);
        settimeofday(&tv, NULL);
        date_set = true;
      }

      rc_set_data(RC_META_LATITUDE,lat);
      rc_set_data(RC_META_LONGITUDE, longitude);
      rc_set_data(RC_META_SPEED, speed_ms*MS_TO_MPH);
      rc_set_data(RC_META_ALTITUDE, elevation_m);
      rc_set_data(RC_META_GPSSATS, n_sats);
      rc_set_data(RC_META_GPSQUAL, myGNSS.getFixType());
      rc_set_data(RC_META_GPSDOP, pdop);      
    } 
    delay(10);
  }
}

void rc_enable_callback(bool enable) {
  if (enable) {
    digitalWrite(RED_LED_PIN, HIGH);
  } else {
    digitalWrite(RED_LED_PIN, LOW);
  }
}

void rc_bt_task(void *arg) {
  rc_bt_reader(&Serial, &rc_enable_callback);
}

void gnss_setup() {
  Wire.begin(UBX_SDA_PIN, UBX_SCL_PIN);
  if (myGNSS.begin()) {
    myGNSS.setDynamicModel(DYN_MODEL_AUTOMOTIVE);
    // Disable non-UBX to save bandwidth and reduce latency on the i2c 
    // link. RTCM is not that expensive, but NMEA is verbose.
    myGNSS.setI2COutput(COM_TYPE_UBX);
    
    myGNSS.setNavigationFrequency(SPARKFUN_UBX_REFRESH_RATE_HZ); 
    myGNSS.setAutoPVT(true);
    // This will optionally persist the settings to NVM on the GNSS device. 
    //myGNSS.saveConfigSelective(VAL_CFG_SUBSEC_IOPORT);
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
}

void rc_bt_setup() {
  char bt_name[32];
  uint8_t mac[6];
  esp_err_t rc = esp_read_mac(mac, ESP_MAC_BT);
  if (rc != ESP_OK) {
    Serial.printf("Failed to read MAC address: %d\n", rc);
    return;
  }

  snprintf(bt_name, sizeof(bt_name), BLUETOOTH_DEVICE_BROADCAST_NAME, mac[3], mac[4], mac[5]);

  rc_handler_init();
  spp_serial_init(bt_name);
  Serial.printf("Bluetooth setup success: %s\n", bt_name);
  xTaskCreate(
    rc_bt_task,
    "bt_reader_task",
    4096,
    NULL, 
    2, 
    NULL
  );
}

void check_shutdown_timer() {
  // TODO: would also need to be wired up to control power on accessories in order to be effective
    if ((millis() - last_data_rx_millis) > SHUTDOWN_IDLE_TIME_MILLIS) {
      Serial.println("[Powering off]"); 
      myGNSS.powerOff(0x0FFFFFFF, 0xEFFF);
      esp_deep_sleep_start();
    }  
}

void setup() {
  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  Serial.write(0); Serial.flush();
  Serial.print("*** uRacePi 2 ***\n");
  
  pinMode(RED_LED_PIN, OUTPUT);

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


  gnss_setup();
  rc_bt_setup();
}

void loop() {

  twai_message_t msg;
  if (twai_receive(&msg, pdMS_TO_TICKS(1)) == ESP_OK) {
    process_send_can_message_esp32(&msg);
    last_data_rx_millis = millis();
  } else {
    check_shutdown_timer();
    delay(1);
  }
}
