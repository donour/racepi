/**************************************************************************
    Copyright 2020-2026 Donour Sizemore

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
#include <driver/twai.h>
#include "rc_podium_protocol.h"
//#include "vehicle_dynamics.h"

#define DEBUG Serial

#define ENABLE_LOTUS_EVORA
#define EVORA_BRAKE_PRESSURE_MAX (690)
#define EVORA_FUEL_CAPACITY_LITERS (60.0f)
#define kPA_TO_PSI (0.14503774f)
#define kmh_to_mps (0.277778f)

uint64_t latest_time = 0;
float latest_yaw_deg = 0.0;

float evora_wheelspeed_kmh(const uint32_t raw) {
  if (raw == 0x3FFF) {
    return 0.0f;
  }
  return raw * 0.0625f;
}


  // Decode CAN 0xB7 external torque requests.
  // data: pointer to message payload (4 or 7 bytes)
  // torque_out: pointer to 3-element output array (Nm, offset +400)
  // dlc: message data length code
  //
  // Torque encoding: 12-bit signed, (value >> 2) + 400 = Nm
  // 0xFFF = not active, output as 0x38F (911)
  //
  // torque_out[0]: cruise control torque target (mode bits = 01)
  // torque_out[1]: ESP stability torque reduction (mode bits = 10)
  // torque_out[2]: extended cruise upper bound (7-byte messages only)
  void decode_0xb7_torque(const uint8_t *data, int16_t *torque_out, uint8_t dlc)
  {
      uint16_t raw[3];

      raw[0] = (data[1] & 0x0F) << 8 | data[0];
      raw[1] = data[2] << 4 | (data[1] >> 4);
      raw[2] = (dlc >= 7) ? ((data[5] & 0x0F) << 8 | data[4]) : 0xFFF;

      for (int i = 0; i < 3; i++) {
          if (raw[i] >= 0xFFF) {
              torque_out[i] = 0x38F;
          } else {
              int16_t s = (raw[i] & 0x800) ? (raw[i] | 0xF000) : raw[i];
              torque_out[i] = (s >> 2) + 400;
          }
      }
  }

int16_t process_send_can_message_esp32(twai_message_t *frame) {
  if (frame == NULL) {
    return -1;
  }

  const uint8_t *data = frame->data;
  const uint8_t dlc = frame->data_length_code;

  switch(frame->identifier) {
#ifdef ENABLE_LOTUS_EVORA
    case 0x0A2:
      if (dlc >= 6 ) {
        // wheelspeeds front + vehicle speed (6-byte message, three 14-bit fields)
        uint32_t lf = data[0] | ((uint32_t)(data[1] & 0x3F) << 8);
        uint32_t rf = (data[1] >> 6) | ((uint32_t)data[2] << 2) | ((uint32_t)(data[3] & 0x0F) << 10);
        rc_set_data(RC_META_WHEEL_SPEED_LF, evora_wheelspeed_kmh(lf));
        rc_set_data(RC_META_WHEEL_SPEED_RF, evora_wheelspeed_kmh(rf));

        uint32_t vs = (data[3] >> 4) | ((uint32_t)data[4] << 4) | ((uint32_t)(data[5] & 0x03) << 12);
        //dynamics_state.speed_ms = vs * kmh_to_mps;

      }
      break;
    case 0x0A4:
      if (dlc >= 5 ) {
        // wheelspeeds rear + brake switch (8-byte message, two 14-bit fields + status)
        uint32_t lr = data[0] | ((uint32_t)(data[1] & 0x3F) << 8);
        uint32_t rr = (data[1] >> 6) | ((uint32_t)data[2] << 2) | ((uint32_t)(data[3] & 0x0F) << 10);
        rc_set_data(RC_META_WHEEL_SPEED_LR, evora_wheelspeed_kmh(lr));
        rc_set_data(RC_META_WHEEL_SPEED_RR, evora_wheelspeed_kmh(rr));
        bool brake_active = (data[4] & 0x03) != 0;
        rc_set_data(RC_META_BRAKE, brake_active ? EVORA_BRAKE_PRESSURE_MAX : 0.0f);
      }
      break;

    case 0x085:
      // steering angle
      if (dlc >= 3) {
        int16_t val = (int16_t)(data[0] | (data[1] << 8));
        float steering_angle = val / 10.0f;

        // drop samples with extreme steering angles that are likely erroneous
        if (steering_angle > -360.0f && steering_angle < 360.0f) {
          rc_set_data(RC_META_STEERING, steering_angle);
        }
        //dynamics_state.steering_wheel_deg = steering_angle;
      }
      break;

    case 0xB7:
      if (dlc >= 3) {
        int16_t torque_result[3];
        decode_0xb7_torque(data, torque_result, dlc);
        rc_set_data(RC_META_TC_TORQUE, torque_result[1]);
      }
      break;

    case 0x102:
      // torque alpha-N net (12-bit unsigned, Nm, no scaling)
      if (dlc >= 3) {
        uint16_t torque_alphaN_net = (data[0] >> 2) | ((uint16_t)(data[1] & 0x0F) << 6);
        if (torque_alphaN_net != 0xFFF) {
          rc_set_data(RC_META_ENGINE_TORQUE, torque_alphaN_net);
        }
      }
      break;
    case 0x114:
      if (dlc >= 6){
        // driver_input_flags[1] (CAN 0x114, byte 4):
        //   bit 0 (0x01): engine start permitted (all start prerequisites met)
        //   bit 1:        unused
        //   bit 2 (0x04): cruise control actively holding speed
        //   bit 3 (0x08): cruise control enabled but not actively controlling
        //   bit 5:4 (0x30): clutch position (00=engaged, 01=partial, 10=disengaged, 11=no sensor)
        //   bit 6 (0x40): traction control disable (TC enabled by driver)
        //   bit 7 (0x80): sport mode active
        //
        // driver_input_flags[0] (CAN 0x114, byte 5):
        //   bit 0 (0x01): brake pedal pressed
        //   bit 1 (0x02): brake light switch active
        //   bit 2 (0x04): sport mode hardware fitted (from COD)
        //   bit 7:3:      unused
        uint8_t driver_input_flags_1 = data[4];
        uint8_t driver_input_flags_0 = data[5];

        bool sport_mode_active = (driver_input_flags_1 & 0x80) != 0;
        bool traction_control_disabled = (driver_input_flags_1 & 0x40) != 0;
        float clutch_position = (driver_input_flags_1 & 0x30) >> 4;
        rc_set_data(RC_META_SPORT_MODE, sport_mode_active ? 1.0f : 0.0f);
        rc_set_data(RC_META_TC_DISABLE, traction_control_disabled ? 1.0f : 0.0f);
        rc_set_data(RC_META_CLUTCH, clutch_position);

        /* This brake info is ignored because it is already logged from the ABS messsage */

        uint16_t tps = (uint8_t)data[3] * 100 / 255;
        rc_set_data(RC_META_TPS, tps);

        uint16_t rpm = (data[0] | (data[1] << 8)) / 4;
        rc_set_data(RC_META_RPM, rpm);
      }
      break;

    case 0x400: // verified 10hz with T6e
      if (dlc >= 6){
        // frame bytes from Evora S2 firmware
        // 4   - fuel level pct
        // 5   - coolant temp
        // 6   - indicator flags

        float fuel_level_liters= data[4] *EVORA_FUEL_CAPACITY_LITERS / 255.0f;
        rc_set_data(RC_META_FUEL_LEVEL, fuel_level_liters);

        int16_t coolant_temp_f = data[5] * 9 / 8 - 40;
        rc_set_data(RC_META_ENGINE_TEMP, coolant_temp_f);
      }
      break;

    case 0x303:
      // IMU (7-byte message: longitudinal accel, lateral accel, yaw rate)
      if (dlc >= 7){

        // The first 12 bits aren't used in this sensor
        // // Longitudinal acceleration (12-bit, bytes 2-3)
        // uint16_t long_raw = ((uint16_t)(data[2] & 0x0F) << 8) | data[3];
        // float long_accel = (long_raw - 2049) * 20385.0f / 100000.0f / 2550.0f;

        // Lateral acceleration (12-bit, bytes 4-5)
        uint16_t lat_raw = ((uint16_t)data[4] << 4) | (data[5] >> 4);
        float lat_accel = (lat_raw - 2049) * 20385.0f / 100000.0f / 2550.0f;

        // Yaw rate (12-bit, bytes 5-6)
        uint16_t yaw_raw = ((uint16_t)(data[5] & 0x0F) << 8) | data[6];
        float yaw = (yaw_raw - 2048) * 8;

        rc_set_data(RC_META_ACCELY, lat_accel);
        rc_set_data(RC_META_YAW, yaw);

        /*
        dynamics_state.yaw_rate_dps = yaw;
        dynamics_state.lat_accel_g = lat_accel;
        update_mu_estimate(&dynamics_state);
        */
      }
      break;
#endif // ENABLE_LOTUS_EVORA

    // OBD-II data
    case 0x7E8:
      if (dlc >= 3) {
        // TODO hand variable length responses
        uint8_t obd_resp_type = data[1];
        uint8_t obd_pid = data[2];
        switch (obd_resp_type) {
          case 0x41:
            if (obd_pid == 0xB) {
              float map = data[3] * kPA_TO_PSI;
              //rc_set_data(RC_META_MAP, map);
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