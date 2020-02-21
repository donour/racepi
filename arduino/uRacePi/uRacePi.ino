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
#include "BluetoothSerial.h"
#include "dl1.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth Classic is not enabled for this build. 
#endif

#define SERIAL_CONSOLE_BAUDRATE (115200)
#define GPS_BAUDRATE            (115200)

static const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "evora";
static const uint32_t MCP2515_QUARTZ_FREQUENCY = 8e6;
static const uint32_t CAN_BITRATE = 5e5;

static const byte MCP2515_SCK  = 5;  
static const byte MCP2515_MOSI = 18;  
static const byte MCP2515_MISO = 19; 
static const byte MCP2515_CS   = 21; 

ACAN2515 can (MCP2515_CS, SPI, 255); // disabled interrupts
BluetoothSerial SerialBT;
    
void setup() {
  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  Serial1.begin(GPS_BAUDRATE);
  SerialBT.begin(BLUETOOTH_DEVICE_BROADCAST_NAME); 
  SPI.begin (MCP2515_SCK, MCP2515_MISO, MCP2515_MOSI);

  ACAN2515Settings settings (MCP2515_QUARTZ_FREQUENCY, CAN_BITRATE);

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

  test_sends();
  
  // TODO: read canbus data from MCP2515 on SPI bus
  
  // TODO: use serial event example to read GPS data from UART

  delay(25);
}
