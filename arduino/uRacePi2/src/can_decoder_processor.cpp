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

#include "BluetoothSerial.h"
#include <driver/twai.h>
#include "rc_podium_protocol.h"

#define DEBUG Serial

#define ACCEL_DIVISOR (38)

#define ENABLE_LOTUS_EVORA

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

  switch(frame->id) { 
#ifdef ENABLE_LOTUS_EVORA
    case 0x085: 
      // steering angle
      if (frame->len >=4) {
        int16_t val = ((int16_t)frame->data16[0]) << 1;
        val >>= 1;
        val /= 10;
        rc_set_data(RC_META_STEERING, val);
      }
      break;
    case 0x114:
      if (frame->len >= 6){

        // bit 40 is brake pedal switch, no pressure reading is provided.
        bool brake_active = ((frame->data[5] & 0x1) != 0);
        rc_set_data(RC_META_BRAKE, brake_active ? 1.0 : 0.0);

        uint16_t tps = (uint8_t)frame->data[3] * 100 / 255;
        rc_set_data(RC_META_TPS, tps);

        uint16_t rpm = frame->data16[0] / 4;
        rc_set_data(RC_META_RPM, rpm);

      }
      break;

    case 0x303:
      // IMU
      if (frame->len >= 6){
        float lat_accel = ((uint8_t)frame->data[4] - 128.0) / ACCEL_DIVISOR;
        float long_accel = 0.0;        
        rc_set_data(RC_META_ACCELX, lat_accel);
        rc_set_data(RC_META_ACCELY, long_accel);
      }
      break;
#endif // ENABLE_LOTUS_EVORA
    default: 
      break; // ignore
  }
  
  return 0;
}

int16_t process_send_can_message_esp32(BluetoothSerial *port, twai_message_t *frame, float power_w) {
  if (frame == 0) return -1;
  common_can_message msg;
  msg.id  = frame->identifier;
  msg.len = frame->data_length_code;
  memcpy(&msg.data, &frame->data, 8);
  return private_send(port, &msg, power_w);
}