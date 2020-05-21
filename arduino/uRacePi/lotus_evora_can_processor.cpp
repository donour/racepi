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

#include <ACAN2515.h>
#include "BluetoothSerial.h"
#include "dl1.h"

#define DEBUG Serial

uint64_t latest_time = 0;

int16_t process_send_can_message(BluetoothSerial *port, CANMessage *frame) {
  if (port == NULL || frame == NULL) {
    return -1;
  }
  dl1_message_t dl1_message;

  // TODO: should this be up to the caller?
  if (millis() > latest_time) {
    latest_time = millis();
    if ( ! get_timestamp_message(&dl1_message, latest_time)) {
      send_dl1_message(&dl1_message, port);
    }
  }

  switch(frame->id) { 

    case 0x085: 
      // steering angle
      if (frame->len >=4) {
        int16_t val = ((int16_t)frame->data16[0]) << 1;
        val >>= 1;
        val /= 10;
        //DEBUG.printf("steer = %d\n", val);
        if ( ! get_steering_angle_message(&dl1_message, val)){
          send_dl1_message(&dl1_message, port);
         }  
      }
      break;
    case 0x114:
      if (frame->len >= 6){
        // TPS
        uint16_t tps = (uint8_t)frame->data[3] * 100 / 255;
        if ( ! get_tps_message(&dl1_message, tps)) {
          send_dl1_message(&dl1_message, port);         
        }
        
        // RPM
        uint16_t rpm = frame->data16[0] / 4;
        if ( ! get_rpm_message(&dl1_message, rpm)) {
          send_dl1_message(&dl1_message, port);
        }  

        // bit 40 is brake pedal switch, no pressure reading is provided.
//        uint16_t brake_pressure_x10 = (frame->data[5] && 0x80) == 1 ? MAX_BRAKE_PRESSURE_BAR*10 : 0;
//        if ( ! get_brake_pressure_message(&dl1_message, brake_pressure_x10)) {
//          send_dl1_message(&dl1_message, port);
//        }
      }
      break;

    case 0x303:
      // IMU
      if (frame->len >= 6){
        float long_accel= (float)frame->data[5] / 32.0;
        float lat_accel= (float)frame->data[4] / 32.0;
        if ( ! get_xy_accel_message(&dl1_message, lat_accel, long_accel)) {
          //DEBUG.printf("%1.2f, %1.2f\n", lat_accel, long_accel);
          //send_dl1_message(&dl1_message, port);
        }    
      }
      break;
    default: 
      break; // ignore
  }
  
  return 0;
}
