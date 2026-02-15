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

#include "BluetoothSerial.h"
#include <driver/twai.h>
#include "rc_podium_protocol.h"

#define DEBUG Serial

#define ENABLE_LOTUS_EVORA
#define EVORA_BRAKE_PRESSURE_MAX (690)
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

uint64_t latest_time = 0;
float latest_yaw_deg = 0.0;

double evora_wheelspeed_kmh(const uint32_t raw) {
  if (raw == 0x3FFF) {
    return 0.0;
  }
  return raw * 0.0625;
}


int16_t private_send(BluetoothSerial *port, common_can_message *frame, float power_w) {
  if (port == NULL || frame == NULL) {
    return -1;
  }

  switch(frame->id) { 
#ifdef ENABLE_LOTUS_EVORA
    case 0x0A2:
      if (frame->len >= 6 ) {
        // wheelspeeds front + vehicle speed (6-byte message, three 14-bit fields)
        uint32_t lf = frame->data[0] | ((uint32_t)(frame->data[1] & 0x3F) << 8);
        uint32_t rf = (frame->data[1] >> 6) | ((uint32_t)frame->data[2] << 2) | ((uint32_t)(frame->data[3] & 0x0F) << 10);
        rc_set_data(RC_META_WHEEL_SPEED_LF, evora_wheelspeed_kmh(lf));
        rc_set_data(RC_META_WHEEL_SPEED_RF, evora_wheelspeed_kmh(rf));
        
        /*
          Ignoring ABS vehicle speed in favor of GPS data

          uint32_t vs = (frame->data[3] >> 4) | ((uint32_t)frame->data[4] << 4) | ((uint32_t)(frame->data[5] & 0x03) << 12);
          rc_set_data(RC_META_SPEED, evora_wheelspeed_kmh(vs) * kmh_to_mps);
        */
        
      }
      break;
    case 0x0A4:
      if (frame->len >= 5 ) {
        // wheelspeeds rear + brake switch (8-byte message, two 14-bit fields + status)
        uint32_t lr = frame->data[0] | ((uint32_t)(frame->data[1] & 0x3F) << 8);
        uint32_t rr = (frame->data[1] >> 6) | ((uint32_t)frame->data[2] << 2) | ((uint32_t)(frame->data[3] & 0x0F) << 10);
        rc_set_data(RC_META_WHEEL_SPEED_LR, evora_wheelspeed_kmh(lr));
        rc_set_data(RC_META_WHEEL_SPEED_RR, evora_wheelspeed_kmh(rr));
        bool brake_active = (frame->data[4] & 0x03) != 0;
        rc_set_data(RC_META_BRAKE, brake_active ? EVORA_BRAKE_PRESSURE_MAX : 0.0);
      }
      break;

    case 0x085: 
      // steering angle
      if (frame->len >= 3) {
        int16_t val = (int16_t)frame->data16[0];
        rc_set_data(RC_META_STEERING, val);
      }
      break;

    case 0x102:
      // torque alpha-N net (12-bit unsigned, Nm, no scaling)
      if (frame->len >= 3) {
        uint16_t torque_alphaN = (frame->data[0] >> 2) | ((uint16_t)(frame->data[1] & 0x0F) << 6);
        if (torque_alphaN != 0xFFF) {
          rc_set_data(RC_META_ENGINE_TORQUE, torque_alphaN);
        }
      }
      break;
    case 0x114:
      if (frame->len >= 6){
        /*
         This brake info is ignored because it is already logged from the ABS messsage.
         
          bool brake_active = ((frame->data[5] & 0x1) != 0);
          rc_set_data(RC_META_BRAKE, brake_active ? EVORA_BRAKE_PRESSURE_MAX : 0.0);
        */

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

        int16_t coolant_temp_f = frame->data[5] * 9 / 8 - 40;
        rc_set_data(RC_META_ENGINE_TEMP, coolant_temp_f);
      }
      break;

    case 0x303:
      // IMU (7-byte message: longitudinal accel, lateral accel, yaw rate)
      if (frame->len >= 7){
        // Longitudinal acceleration (12-bit, bytes 2-3)
        uint16_t long_raw = ((uint16_t)(frame->data[2] & 0x0F) << 8) | frame->data[3];
        float long_accel = (long_raw - 2049) * 20385.0 / 100000.0 / 2550.0;

        // Lateral acceleration (12-bit, bytes 4-5)
        uint16_t lat_raw = ((uint16_t)frame->data[4] << 4) | (frame->data[5] >> 4);
        float lat_accel = (lat_raw - 2049) * 20385.0 / 100000.0 / 2550.0;

        // Yaw rate (12-bit, bytes 5-6)
        uint16_t yaw_raw = ((uint16_t)(frame->data[5] & 0x0F) << 8) | frame->data[6];
        float yaw = (yaw_raw - 2048) * 8;

        rc_set_data(RC_META_ACCELX, long_accel);
        rc_set_data(RC_META_ACCELY, lat_accel);
        rc_set_data(RC_META_YAW, yaw);
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