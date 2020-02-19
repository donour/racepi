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
#include "BluetoothSerial.h"
#include "dl1.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth Classic is not enabled for this build. 
#endif

#define SERIAL_CONSOLE_BAUDRATE (115200)
#define GPS_BAUDRATE            (115200)

const char BLUETOOTH_DEVICE_BROADCAST_NAME[] = "evora";

BluetoothSerial SerialBT;

long start_time;

long uptime() {
  return millis() - start_time;
}
    
void setup() {
  Serial.begin(SERIAL_CONSOLE_BAUDRATE);
  Serial1.begin(GPS_BAUDRATE);
  SerialBT.begin(BLUETOOTH_DEVICE_BROADCAST_NAME); 

  start_time = millis();
}

void test_sends() { 
  dl1_message_t dl1_message;

  if ( ! get_timestamp_message(&dl1_message, uptime())) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_speed_message(&dl1_message, millis() % 200, 10)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_gps_pos_message(&dl1_message, 1000, 1000, 10)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_tps_message(&dl1_message, (millis()/1000) % 101)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }

  if ( ! get_rpm_message(&dl1_message, millis() % 10001)) {
    send_dl1_message(&dl1_message, &SerialBT);
  }  
}

void loop() {

  test_sends();
  
  // TODO: read canbus data from MCP2515 on SPI bus
  
  // TODO: use serial event example to read GPS data from UART

  delay(100);
}
