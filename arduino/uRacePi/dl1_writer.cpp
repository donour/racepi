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

#include <string.h>
#include "dl1.h"

#define FAIL_ON_NULL(v) ({if(v == NULL) return -1;})

unsigned char checksum(unsigned char *data, unsigned int length) {
  unsigned char cs = 0;
  for (int i = 0; i < length; i++) {
    cs += data[i];
  }
  return cs & 0xFF;
}

void set_checksum(dl1_message_t *message) {
  if(message != NULL) {
    message->checksum = 0;
    for (int i = 0; i < message->length; i++) {
      message->checksum += message->data[i];    
    }
  }
}


int send_dl1_message(dl1_message_t *message, BluetoothSerial *port) {
  FAIL_ON_NULL(message);
  FAIL_ON_NULL(port);

  // TODO: This should be taskEnterCritical if using RTOS tasks
  int rc1 = port->write(message->data, message->length);
  if (rc1 < 0) return rc1;
  int rc2 = port->write(message->checksum);
  if (rc2 < 0) return rc2;
  return rc1+rc2;          
}

//////////////////////////////////////////////////////////////////////////
// Message construction helpers, byte stuffing these buffers is the 
// simplest way to ensure that we get the byte ordering we want...strange
// that several of the messages have an odd number of bytes per value.

int get_timestamp_message(dl1_message_t *message, unsigned long timestamp) {
  FAIL_ON_NULL(message);

  // DL1 time is in centiseconds, not millis
  unsigned int t = timestamp / 10;
  
  message->data[0] = TIMESTAMP_MESSAGE_ID;
  message->data[1] = t>>16;
  message->data[2] = t>>8;
  message->data[3] = t & 0xFF;
  message->length = 4;
  set_checksum(message);
  return 0; 
}

int get_speed_message(dl1_message_t *message, unsigned int speed_ms_x100, unsigned short accuracy_ms_x100) {
  FAIL_ON_NULL(message);

  message->data[0] = GPS_SPEED_MESSAGE_ID;
  message->data[1] = speed_ms_x100 >> 24;
  message->data[2] = speed_ms_x100 >> 16;
  message->data[3] = speed_ms_x100 >> 8;
  message->data[4] = speed_ms_x100;
  message->data[5] = 0;
  message->data[6] = accuracy_ms_x100 >> 16;
  message->data[7] = accuracy_ms_x100 >> 8;
  message->data[8] = accuracy_ms_x100; 
  message->length = 9;
  set_checksum(message);
  return 0; 

}

int get_rpm_message(dl1_message_t *message, unsigned short rpm) {
  FAIL_ON_NULL(message);
  
  float val = (float)rpm/60.0;
  if (val > 0.0) {
    val = 1.0/val;
  }
  val *= DL1_PERIOD_CONSTANT;
  int freq = (int)val; // TODO, this isn't really frequency
  message->data[0] = RPM_MESSAGE_ID;
  message->data[1] = freq >> 16;
  message->data[2] = freq >> 8;
  message->data[3] = freq;
  message->length = 4;
  set_checksum(message);
  return 0;   
}

int get_gps_pos_message(dl1_message_t *message, int lat_xe7, int long_xe7, int error_xe3) {
  FAIL_ON_NULL(message);

  message->data[0] = GPS_POS_MESSAGE_ID;
  *(int*)(&message->data[1]) = lat_xe7;
  *(int*)(&message->data[5]) = long_xe7;
  *(int*)(&message->data[9]) = error_xe3;
  message->length = 13;
  set_checksum(message);
  return 0;     
}

int get_tps_message(dl1_message_t *message, unsigned short tps) {
  FAIL_ON_NULL(message);

  unsigned short voltage_x1000 = tps*1000*5/100;
  message->data[0] = TPS_MESSAGE_ID;
  message->data[1] = voltage_x1000 >> 8;
  message->data[2] = voltage_x1000;
  message->length = 3;
  set_checksum(message);
  return 0;     
}

int get_steering_angle_message(dl1_message_t *message, short angle_deg) {
  FAIL_ON_NULL(message);
  
  angle_deg *= 10;  
  message->data[0] = STEERING_ANGLE_ID;
  message->data[1] = angle_deg >> 8;
  message->data[2] = angle_deg;
  message->length = 3;
  set_checksum(message);
  return 0;         
}
