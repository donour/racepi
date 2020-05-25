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

void test_sends(BluetoothSerial *port) { 
  dl1_message_t dl1_message;


  if ( ! get_speed_message(&dl1_message, (millis()/10) % 200, 10)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_gps_pos_message(&dl1_message, 41000000, 3400000, 1200)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_tps_message(&dl1_message, (millis()/100) % 101)) {
    send_dl1_message(&dl1_message, port, true);
  }

  uint16_t brake_pressure_x10 = 1<< (((millis()/10)/15) % 16);
  if ( ! get_brake_pressure_message(&dl1_message, brake_pressure_x10)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_rpm_message(&dl1_message,  sin(millis()/3000.0)*4500 + 4500)) {
    send_dl1_message(&dl1_message, port, true);
  }  

  if ( ! get_steering_angle_message(&dl1_message, sin(millis()/3000.0)*200)){
    send_dl1_message(&dl1_message, port, true);
  }  

  if ( ! get_xy_accel_message(&dl1_message, sin(millis()/3000.0)/1.1, cos(millis()/3000.0)/1.1)) {
    send_dl1_message(&dl1_message, port, true);
  }    
}
