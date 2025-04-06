/**************************************************************************
    Copyright 2020-2025 Donour Sizemore

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

#include <math.h>
#include <driver/twai.h>
#include "BluetoothSerial.h"
#include "rc_podium_protocol.h"

#define DEBUG Serial

#define ACCEL_DIVISOR (38)

#define ENABLE_LOTUS_EVORA
#define EVORA_BRAKE_PRESSURE_MAX (690)
#define EVORA_FRONT_WHEEL_TICKS_PER_REV (0x3E8*1.239)
#define EVORA_REAR_WHEEL_TICKS_PER_REV (0x3FC*1.1776)
#define kPA_TO_PSI (0.14503773773020922)
#define kmh_to_mps (0.277778)

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

/* TODO: calculate understeer
  uint16_t evora_wheelbase_mm = 2575;
  uint16_t evora steering_ratio_x10 = 160; // 16:1
  understeer = actual_yaw / requested yaw

  actual yaw: measured

  requested raw:  %/time of turning circle * 2*pi
  %/time turning circle: speed / turning circle size
  speed: measured
  turning circle size: turn radius * 2*pi
  turn radius : wheelbase / sin(steering_angle)

*/

uint64_t latest_time = 0;
float latest_yaw_deg = 0.0;
float latest_steering_angle = 0.0;

double evora_wheelspeed_cal(const uint32_t raw, const uint32_t pulses_per_rev) {
  if (raw == 0x3FFF) {
    return 0.0;
  }
  uint32_t scaled = raw * 0x32 >> 3;
  scaled = (pulses_per_rev * scaled) / 1000;
  float scaled_f = (float)scaled / (1000.0); // TODO this needs scaling to gps corrected speed
  return (double)scaled_f;
}

float lastest_steering_angle_rad = 0.0;

double calc_understeer(float steering_angle_rad, float wheelbase_m, float speed_ms, float actual_yal_rad) {
  float requested_yaw_rad = 0.0;
  if (steering_angle_rad > 0.08) {
    float turn_radius_m = wheelbase_m / sin(steering_angle_rad);
    float turning_circle_size_m = turn_radius_m * 2.0 * M_PI;
    float turning_circle_pct = speed_ms / turning_circle_size_m;
    requested_yaw_rad = turning_circle_pct * 2.0 * M_PI;
  }
  return (actual_yal_rad - requested_yaw_rad) / actual_yal_rad;
}


int16_t private_send(BluetoothSerial *port, common_can_message *frame, float power_w) {
  if (port == NULL || frame == NULL) {
    return -1;
  }

  switch(frame->id) { 
#ifdef ENABLE_LOTUS_EVORA
    case 0x0A2:
      if (frame->len >= 4 ) {
        // wheelspeeds front
        uint32_t lf = (frame->data[1] & 0x3f) << 8 | frame->data[0];
        uint32_t rf = (frame->data[1] & 0xC0) >> 6 | (frame->data[3] & 0xF) << 10 | frame->data[2] << 2;
        rc_set_data(RC_META_WHEEL_SPEED_LF, evora_wheelspeed_cal(lf, EVORA_FRONT_WHEEL_TICKS_PER_REV));
        rc_set_data(RC_META_WHEEL_SPEED_RF, evora_wheelspeed_cal(rf, EVORA_FRONT_WHEEL_TICKS_PER_REV));
      }
      break;
    case 0x0A4:
      if (frame->len >= 4 ) {
        // wheelspeeds rear
        uint32_t lr = (frame->data[1] & 0x3f) << 8 | frame->data[0];
        uint32_t rr = (frame->data[1] & 0xC0) >> 6 | (frame->data[3] & 0xF) << 10 | frame->data[2] << 2;
        rc_set_data(RC_META_WHEEL_SPEED_LR, evora_wheelspeed_cal(lr, EVORA_REAR_WHEEL_TICKS_PER_REV));
        rc_set_data(RC_META_WHEEL_SPEED_RR, evora_wheelspeed_cal(rr, EVORA_REAR_WHEEL_TICKS_PER_REV));
      }
      break;

    case 0x085: 
      // steering angle
      if (frame->len >=4) {
        int16_t val = ((int16_t)frame->data16[0]) << 1;
        val >>= 1;
        rc_set_data(RC_META_STEERING, val/10);
        lastest_steering_angle_rad = (val/10.0) * M_PI / 180.0;
      }
      break;

    case 0x102:
      // torque limits
      if (frame->len >= 3) {
        // two values packed into 3 bytes
        uint16_t torque_limit = ((uint16_t)(frame->data[0]) >> 2) | (((uint16_t)(frame->data[1] & 0x0F)) << 6);
        uint16_t raw_engine_torque = ((uint16_t)(frame->data[1] & 0xF0) >> 4) | ((uint16_t)frame->data[2] << 4);
        uint16_t engine_torque = raw_engine_torque + 400;
        rc_set_data(RC_META_TORQUE_LIMIT, torque_limit);
        rc_set_data(RC_META_ENGINE_TORQUE, engine_torque);
      }
      break;
    case 0x114:
      if (frame->len >= 6){
        // frame bytes from Evora S2 firmware
        // 0:1 - RPM
        // 2:  - 0
        // 3:  - TPS
        // 4:  - driver input switches
        // 5:  - unknown
        // 6:7 - zero

        // bit 40 is brake pedal switch, no pressure reading is provided.
        bool brake_active = ((frame->data[5] & 0x1) != 0);
        rc_set_data(RC_META_BRAKE, brake_active ? EVORA_BRAKE_PRESSURE_MAX : 0.0);

        uint16_t tps = (uint8_t)frame->data[3] * 100 / 255;
        rc_set_data(RC_META_TPS, tps);

        uint16_t rpm = frame->data16[0] / 4;
        rc_set_data(RC_META_RPM, rpm);

      }
      break;

    case 0x400: // verified 10hz with T6e
      if (frame->len >= 6){
        // frame bytes from Evora S2 firmware   
        // 4   - fuel level pct
        // 5   - coolant temp
        // 6   - indicator flags

        uint8_t fuel_level = frame->data[4] * 100 / 255;
        rc_set_data(RC_META_FUEL_LEVEL, fuel_level);

        uint8_t coolant_temp = frame->data[5];
        rc_set_data(RC_META_ENGINE_TEMP, coolant_temp);
      }
      break;

    case 0x303:
      // IMU
      if (frame->len >= 6){
        float lat_accel = ((uint8_t)frame->data[4] - 128.0) / ACCEL_DIVISOR;
        float long_accel = 0.0;        
        rc_set_data(RC_META_ACCELX, lat_accel);
        rc_set_data(RC_META_ACCELY, long_accel);

        // TODO lookup yaw channel and calculate understeer
      }
      break;
#endif // ENABLE_LOTUS_EVORA

    // OBD-II data
    case 0x7E8:
      if (frame->len >= 3) {
        // TODO hand variable length responses         
        uint8_t obd_resp_type = frame->data[1];
        uint8_t obd_pid = frame->data[2];
        switch (obd_resp_type) {
          case 0x41:
            if (obd_pid == 0xB) {
              double map = frame->data[3] * kPA_TO_PSI;
              rc_set_data(RC_META_MAP, map);
            }
            break;
          // Mode $22 not implemented
            // case 0x62:
            //  if (obd_pid == 0x2) {}
            //  break;
          default:
            break;
        }
      }
      break;
      
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