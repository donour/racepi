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

#include <string.h>
#include <math.h> // TODO remove me
#include <ACAN2515.h>
#include "SparkFun_Ublox_Arduino_Library.h"
#include "BluetoothSerial.h"
#include "dl1.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth Classic is not enabled for this build. 
#endif

#define SERIAL_CONSOLE_BAUDRATE (115200)
#define GPS_BAUDRATE            (115200)

#define DEBUG_PORT (Serial)
#define UBX_PORT   (Serial1)

static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "evora";
static const uint32_t MCP2515_QUARTZ_FREQUENCY = 8e6;
static const uint32_t CAN_BITRATE = 5e5;

static const byte MCP2515_SCK  = 5;  
static const byte MCP2515_MOSI = 18;  
static const byte MCP2515_MISO = 19; 
static const byte MCP2515_CS   = 21; 

ACAN2515 canbus (MCP2515_CS, SPI, 255); // disabled interrupts
BluetoothSerial SerialBT;
SFE_UBLOX_GPS ubx_gps;
dl1_message_t dl1_message;

int16_t setup_mcp2515(ACAN2515 *can, HardwareSerial *debug_port) {

  ACAN2515Settings settings(MCP2515_QUARTZ_FREQUENCY, CAN_BITRATE);

  // TODO: setup incoming filters

  const uint16_t rc = canbus.begin(settings, NULL);
  if (rc != 0) {
    debug_port->printf("(MCP2515) setup errr: %x", rc);
    return rc;
  }
  debug_port->printf("(MCP2515) bit rate: %d", settings.actualBitRate ());
  return 0;
}

bool try_ublox_gnss_connect(uint32_t baud) {
  DEBUG_PORT.printf("(GNSS/uBlox): attempting to connect (%d baud)\n", baud); 
  UBX_PORT.begin(baud);
  return ubx_gps.begin(UBX_PORT);
}

int16_t setup_ublox_gnss() { 

  const uint32_t test_rates[] = {4800, 9600, 38400};
  boolean setup_complete = false;

  while ( ! try_ublox_gnss_connect(GPS_BAUDRATE)) {     

    // try each available baudrate
    // if any rates succeed update config and start over
    int i = 0;
    do {
      // check if we have exhausted baudrates to try
      if (i >= sizeof(test_rates)/sizeof(uint32_t)) {
        return -1;
      }
      DEBUG_PORT.printf("(GNSS/uBlox): failed\n"); 
      delay(200);
      i++;
    } while ( ! try_ublox_gnss_connect(test_rates[i]));
    DEBUG_PORT.printf("(GNSS/uBlox): Connection success, switching bitrate to %d\n", GPS_BAUDRATE); 
    ubx_gps.setSerialRate(GPS_BAUDRATE);
    delay(500);
  }

  DEBUG_PORT.printf("(GNSS/uBlox): Connection success, writing new configuration\n"); 
  // set config

  ubx_gps.setUART1Output(COM_TYPE_UBX);
  ubx_gps.setI2COutput(COM_TYPE_UBX);
  ubx_gps.powerSaveMode(false); 
  ubx_gps.setAutoPVT(true);
  ubx_gps.setNavigationFrequency(15);
  if ( ! ubx_gps.setDynamicModel(DYN_MODEL_AUTOMOTIVE)) {
    DEBUG_PORT.printf("(GNSS/uBlox): Failed to update dynamic model\n"); 
  }

  ubx_gps.saveConfiguration();
  return 0; 
}

// check for any received GPS data and send to clients it exists
// return 0 if data was sent, non zero on failure
int16_t update_gnss() { 
  if (ubx_gps.getPVT()){
    if ( ! get_timestamp_message(&dl1_message, millis())) {
      send_dl1_message(&dl1_message, &SerialBT);
    }

    if ( ! get_speed_message(&dl1_message, ubx_gps.getGroundSpeed()/10, 1)) {
      send_dl1_message(&dl1_message, &SerialBT);
    }
    if ( ! get_gps_pos_message(
      &dl1_message, 
      ubx_gps.getLatitude(), 
      ubx_gps.getLongitude(), 
      ubx_gps.getHorizontalAccuracy())) {
      send_dl1_message(&dl1_message, &SerialBT);
    }

    return 0;
  }
  return -1;  
}
    
void setup() {
  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
 
  SerialBT.begin(BLUETOOTH_DEVICE_BROADCAST_NAME); 
  SPI.begin(MCP2515_SCK, MCP2515_MISO, MCP2515_MOSI);

  int16_t mcp_rc = setup_mcp2515(&canbus, &Serial); 
  if (mcp_rc != 0) {
    // TODO handle mcp2515 setup errors
  }
  int16_t gnss_rc = setup_ublox_gnss(); 
  if (gnss_rc != 0) {
    // TODO handle gnss setup errors
  }
}


void test_sends() { 
  dl1_message_t dl1_message;

  if ( ! get_timestamp_message(&dl1_message, millis())) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_speed_message(&dl1_message, (millis()/10) % 200, 10)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_gps_pos_message(&dl1_message, 1000, 1000, 1200)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_tps_message(&dl1_message, (millis()/100) % 101)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  uint16_t rpm = ((sin(millis()/3000.0) + 1.0)*5000.0);
  if ( ! get_rpm_message(&dl1_message, rpm)) {
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
  int rc = 0;
  test_sends();
  
  // TODO: read canbus data from MCP2515 on SPI bus
  rc |= update_gnss();

  if (rc != 0) {
     // no work was done this cycle
    delay(25);
  }
}
