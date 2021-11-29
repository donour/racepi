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

#include "dl1.h"
#include "tests.h"

void test_dl1_sends(BluetoothSerial *port) { 
  char buf[2048];
  dl1_message_t dl1_message;

//  sprintf(buf, "{\"Speed\": %d}", (millis()/10) % 200);
//  port->write((const uint8_t*)buf, strlen(buf));
//  sprintf(buf, "{\"Latitude\": 41000000}");
//  port->write((const uint8_t*)buf, strlen(buf));
//  sprintf(buf, "{\"Longitude\": 3400000}");
//  port->write((const uint8_t*)buf, strlen(buf));
//
//  //sprintf(buf, "{\"s\": {\"t\":%d, \"Speed\": %d, \"Latitude\": 41000000, \"Longitude\": 3400000}}", millis(),(millis()/10) % 200 );
//  sprintf(buf, "{\"meta\":[{\"nm\":\"Speed\",\"ut\":\"mps\",\"sr\":1},{\"nm\":\"Latitude\",\"ut\":\"Deg\",\"sr\":1},{\"nm\":\"Longitude\",\"ut\":\"Deg\",\"sr\":1}]}\r\n");
//  port->write((const uint8_t*)buf, strlen(buf));
//
//  sprintf(buf, "{\"s\":{\"t\":%d,\"d\":[1.1,41.123,36.123]}}\r\n", millis());
//  port->write((const uint8_t*)buf, strlen(buf));


  if ( ! get_speed_message(&dl1_message, (millis()/10) % 200, 10)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_gps_pos_message(&dl1_message, 41000000, 3400000, 1200)) {
    send_dl1_message(&dl1_message, port, false);
  }

  if ( ! get_gps_altitude_message(&dl1_message, millis() % 2000, 123)) {
    send_dl1_message(&dl1_message, port, false);
  }

  if ( ! get_tps_message(&dl1_message, (millis()/100) % 101)) {
    send_dl1_message(&dl1_message, port, false);
  }

//  uint16_t brake_pressure_x10 = millis() % 10000;//1<< (((millis()/10)/15) % 16);
//  if ( ! get_brake_pressure_message(&dl1_message, brake_pressure_x10)) {
//    send_dl1_message(&dl1_message, port, false);
//  }

  if ( ! get_rpm_message(&dl1_message,  sin(millis()/3000.0)*4500 + 4500)) {
    send_dl1_message(&dl1_message, port, false);
  }  

  if ( ! get_steering_angle_message(&dl1_message, sin(millis()/3000.0)*200)){
    send_dl1_message(&dl1_message, port, false);
  }  

  if ( ! get_xy_accel_message(&dl1_message, sin(millis()/3000.0)/1.1, cos(millis()/3000.0)/1.1)) {
    send_dl1_message(&dl1_message, port, false);
  } 
}
