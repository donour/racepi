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

#include "BluetoothSerial.h"

const char XYACCEL_MESSAGE_ID = 8;
const char TIMESTAMP_MESSAGE_ID = 9;
const char GPS_POS_MESSAGE_ID = 10;
const char GPS_SPEED_MESSAGE_ID = 11;
const char GPS_COURSE_MESSAGE_ID = 56;
const char RPM_MESSAGE_ID = 18;
const char TPS_MESSAGE_ID = 27;//  # Analog 1
const char BRAKE_MESSAGE_ID = 25;//  # Analog 2
const char STEERING_ANGLE_ID = 93;
const char EXT_PRESSURE_MESSAGE_ID = 94;
const char WHEEL_SPEED_LF_ID = 58;
const char WHEEL_SPEED_RF_ID = 59;
const char WHEEL_SPEED_LR_ID = 60;
const char WHEEL_SPEED_RR_ID = 61;
const char Z_ACCEL_MESSAGE_ID = 92;

const int DL1_PERIOD_CONSTANT = 6e6;

typedef struct {
  unsigned char data[16];
  short length;
  unsigned char checksum;
} dl1_message_t;

int send_dl1_message(dl1_message_t *message, BluetoothSerial *port);

int get_timestamp_message(dl1_message_t *message, unsigned long timestamp);
int get_rpm_message(dl1_message_t *message, unsigned short rpm);
int get_speed_message(dl1_message_t *message, unsigned int speed_ms_x100, unsigned short accuracy_ms_x100);
int get_gps_pos_message(dl1_message_t *message, int lat_x7, int long_x7, int error_x3);
int get_tps_message(dl1_message_t *message, unsigned short tps);
int get_steering_angle_message(dl1_message_t *message, short);
