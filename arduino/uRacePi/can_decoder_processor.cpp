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

#include <ACAN2515.h>
#include "BluetoothSerial.h"
#include "dl1.h"
#include <driver/can.h>

#define DEBUG Serial

//#define ACCEL_DIVISOR (8000.0)
#define ACCEL_DIVISOR (38)

#define ENABLE_LOTUS_EVORA
// #define ENABLE_BRZ_FRS

class common_can_message {
  public : uint32_t id = 0;  
  public : uint8_t idx = 0;  
  public : uint8_t len = 0;  
  public : union {
    uint64_t data64; 
    uint32_t data32 [2]; 
    uint16_t data16 [4]; 
    float    dataFloat [2];
    uint8_t  data   [8] = {0, 0, 0, 0, 0, 0, 0, 0};
  };
};

uint64_t latest_time = 0;
float latest_yaw_deg = 0.0;

// used for calculating oversteer
// #define STEER_RATIO (1.0/15.0)
// float latest_steering_angle = 0;
// float ackermann_yaw(const float steering_angle, const float wheelbase, const float velocity) {

//   // TODO finish
//   const float wheel_angle = steering_angle * STEER_RATIO;
//   return velocity*tan(wheel_angle) / wheelbase;
// }

// float yaw_intended(const float steering_angle, const float wheelbase, const float velocity) {
//   // TODO finish
//   const float wheel_angle = steering_angle * STEER_RATIO;
//   return velocity * wheel_angle / (2 * wheelbase);  
// }

// float surface_limit(const float lat_accel, float velocity) {
//   return lat_accel / velocity;
// }


int16_t private_send(BluetoothSerial *port, common_can_message *frame, float power_w) {
  if (port == NULL || frame == NULL) {
    return -1;
  }
  dl1_message_t dl1_message;

  switch(frame->id) { 
#ifdef ENABLE_LOTUS_EVORA
    case 0x085: 
      // steering angle
      if (frame->len >=4) {
        int16_t val = ((int16_t)frame->data16[0]) << 1;
        val >>= 1;
        val /= 10;
        if ( ! get_steering_angle_message(&dl1_message, val)){
          send_dl1_message(&dl1_message, port, true);
         }  
      }
      break;
    case 0x114:
      if (frame->len >= 6){

        // bit 40 is brake pedal switch, no pressure reading is provided.
        bool brake_active = ((frame->data[5] & 0x1) != 0);
        /* brake pressure message is broken in solostorm client; this message is disabled
        uint16_t brake_pressure_x10 = (frame->data[5] & 0x1) == 0 ? 0 : MAX_BRAKE_PRESSURE_BAR*10;
        if ( ! get_brake_pressure_message(&dl1_message, brake_pressure_x10)) {
          send_dl1_message(&dl1_message, port, false);
        }*/

        // TPS
        uint16_t tps = (uint8_t)frame->data[3] * 100 / 255;
        // overload TPS with brake sensor, 0-50 is brake overlap, 50-100 is Throttle only
        tps /= 2;
        if (! brake_active) {
          tps += 50;
        }
        if ( ! get_tps_message(&dl1_message, tps)) {
          send_dl1_message(&dl1_message, port, true);
        }

        // RPM
        uint16_t rpm = frame->data16[0] / 4;
        if ( ! get_rpm_message(&dl1_message, rpm)) {
          send_dl1_message(&dl1_message, port, false);
        }

      }
      break;

    case 0x303:
      // IMU
      if (frame->len >= 6){
        // Reference value from Bosch manual
        //float lat_accel = (int16_t)((frame->data16[2]+(0x8000))) * 0.0001274; // g
        //float long_accel = 0;
        //float yaw1 = ((int16_t)(frame->data16[0]+(0x8000))) * 0.005 ; // deg/s^2
        // float lat_accel = (((int16_t)frame->data16[2] )& 0xFFFFFF00) / ACCEL_DIVISOR;
        // float long_accel = power_w * 0.0000134102 ; // hp * 10^-2
        // float yaw = (((int16_t)frame->data16[3] )& 0x00FFFFFF) - 2048.0;
        // latest_yaw_deg = yaw;

        float lat_accel = ((uint8_t)frame->data[4] - 128.0) / ACCEL_DIVISOR;
        //float long_accel = ((int8_t)frame->data[2]) / ACCEL_DIVISOR;
        float long_accel = 0.0;        

        if ( ! get_xy_accel_message(&dl1_message, lat_accel, long_accel)) {
          send_dl1_message(&dl1_message, port, true);
        }    
      }
      break;
#endif // ENABLE_LOTUS_EVORA

#ifdef ENABLE_BRZ_FRS
    case 0xD0:
      // Steering able
      if (frame->len >= 4) {
        // TODO: Why am I doing these shifts??
        int16_t val = ((int16_t)frame->data16[0]) << 1;
        val >>= 1;
        val /= 10;
        if ( ! get_steering_angle_message(&dl1_message, val)){
          send_dl1_message(&dl1_message, port, true);
         }          
      }
      break;
    case 0xD1:
      if (frame->len >=3) {
        uint8_t brake_pressure = (uint8_t)frame->data[2];
      }
      break;
    case 0x140:
      if (frame->len >=8) {
        uint16_t tps = (uint8_t)frame->data[0] * 100 / 255;
        if ( ! get_tps_message(&dl1_message, tps)) {
          send_dl1_message(&dl1_message, port, true);
        }
      }
      break;            
#endif //ENABLE_BRZ_FRS
    default: 
      break; // ignore
  }
  
  return 0;
}

int16_t process_send_can_message(BluetoothSerial *port, CANMessage *frame) {
  if (frame == 0) return -1;
  common_can_message msg;
  msg.id  = frame->id;
  msg.idx = frame->idx;
  msg.len = frame->len;
  msg.data64 = frame->data64;
  return private_send(port, &msg, 0.0);
}

int16_t process_send_can_message_esp32(BluetoothSerial *port, can_message_t *frame, float power_w) {
  if (frame == 0) return -1;
  common_can_message msg;
  msg.id  = frame->identifier;
  msg.len = frame->data_length_code;
  memcpy(&msg.data, &frame->data, 8);
  return private_send(port, &msg, power_w);
}
