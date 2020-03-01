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

#ifndef __DL1_
#define __DL1_

#include "BluetoothSerial.h"

static const char XYACCEL_MESSAGE_ID = 8;
static const char TIMESTAMP_MESSAGE_ID = 9;
static const char GPS_POS_MESSAGE_ID = 10;
static const char GPS_SPEED_MESSAGE_ID = 11;
static const char GPS_COURSE_MESSAGE_ID = 56;
static const char RPM_MESSAGE_ID = 18;
static const char TPS_MESSAGE_ID = 27;//  # Analog 1
static const char BRAKE_MESSAGE_ID = 25;//  # Analog 2
static const char STEERING_ANGLE_ID = 93;
static const char EXT_PRESSURE_MESSAGE_ID = 94;
static const char WHEEL_SPEED_LF_ID = 58;
static const char WHEEL_SPEED_RF_ID = 59;
static const char WHEEL_SPEED_LR_ID = 60;
static const char WHEEL_SPEED_RR_ID = 61;
static const char Z_ACCEL_MESSAGE_ID = 92;

static const int32_t DL1_PERIOD_CONSTANT = 6e6;

typedef struct {
  unsigned char data[16];
  int16_t length;
  unsigned char checksum;
} dl1_message_t;

int32_t send_dl1_message(dl1_message_t *message, BluetoothSerial *port);

int32_t get_timestamp_message(dl1_message_t *message, uint64_t timestamp);
int32_t get_rpm_message(dl1_message_t *message, uint16_t rpm);
int32_t get_speed_message(dl1_message_t *message, uint32_t speed_ms_x100, uint32_t accuracy_ms_x100);
int32_t get_gps_pos_message(dl1_message_t *message, int32_t lat_xe7, int32_t long_xe7, int32_t error_xe3);
int32_t get_tps_message(dl1_message_t *message, uint16_t tps);
int32_t get_steering_angle_message(dl1_message_t *message, int16_t angle_deg);
int32_t get_xy_accel_message(dl1_message_t *message, float x_accel, float y_accel);


#endif // __DL_1
