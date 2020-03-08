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

static SemaphoreHandle_t message_write_lock;


unsigned char checksum(unsigned char *data, uint32_t length) {
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

int16_t dl1_init() {
  message_write_lock = xSemaphoreCreateMutex();
}


int16_t send_dl1_message(dl1_message_t *message, BluetoothSerial *port) {
  FAIL_ON_NULL(message);

  if (xSemaphoreTake(message_write_lock, portMAX_DELAY) == 0) {
    return -1;
  }
  int rc = port->write(message->data, message->length);
  if (rc >=0) {
    rc += port->write(message->checksum);
  }
  xSemaphoreGive(message_write_lock);
  return rc;
  
}

//////////////////////////////////////////////////////////////////////////
// Message construction helpers, byte stuffing these buffers is the 
// simplest way to ensure that we get the byte ordering we want...strange
// that several of the messages have an odd number of bytes per value.
//
// Message values are in network order (big endian), but my devices (esp32)
// are little endian. TODO: add support for big endian host order

int32_t get_timestamp_message(dl1_message_t *message, uint64_t timestamp) {
  FAIL_ON_NULL(message);

  // DL1 time is in centiseconds, not millis
  uint32_t t = timestamp / 10;
  
  message->data[0] = TIMESTAMP_MESSAGE_ID;
  message->data[1] = t>>16;
  message->data[2] = t>>8;
  message->data[3] = t & 0xFF;
  message->length = 4;
  set_checksum(message);
  return 0; 
}

int32_t get_speed_message(dl1_message_t *message, uint32_t speed_ms_x100, uint32_t accuracy_ms_x100) {
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

int32_t get_rpm_message(dl1_message_t *message, uint16_t rpm) {
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

int32_t get_gps_pos_message(dl1_message_t *message, int32_t lat_xe7, int32_t long_xe7, int32_t error_xe3) {
  FAIL_ON_NULL(message);

  message->data[0] = GPS_POS_MESSAGE_ID;
  message->data[1] = lat_xe7 >> 24;
  message->data[2] = lat_xe7 >> 16;
  message->data[3] = lat_xe7 >> 8;
  message->data[4] = lat_xe7;

  message->data[5] = long_xe7 >> 24;
  message->data[6] = long_xe7 >> 16;
  message->data[7] = long_xe7 >> 8;
  message->data[8] = long_xe7;

  message->data[ 9] = error_xe3 >> 24;
  message->data[10] = error_xe3 >> 16;
  message->data[11] = error_xe3 >> 8;
  message->data[12] = error_xe3;

  message->length = 13;
  set_checksum(message);
  return 0;     
}

int32_t get_tps_message(dl1_message_t *message, uint16_t tps) {
  FAIL_ON_NULL(message);

  int16_t voltage_x1000 = tps*1000*5/100;
  message->data[0] = TPS_MESSAGE_ID;
  message->data[1] = voltage_x1000 >> 8;
  message->data[2] = voltage_x1000;
  message->length = 3;
  set_checksum(message);
  return 0;     
}

int32_t get_steering_angle_message(dl1_message_t *message, int16_t angle_deg) {
  FAIL_ON_NULL(message);
  
  unsigned char b2=0, b3=0;
  angle_deg *= 10;  
  if (angle_deg < 0) {
    angle_deg += 65536;      
    b3 = 0x80;
  }
  b2 = angle_deg & 0xFF;
  b3 |= ((angle_deg >> 8) & 0xFF);

  message->data[0] = STEERING_ANGLE_ID;
  message->data[2] = 0x3;
  message->data[2] = b2;
  message->data[3] = b3;
  message->length = 4;
  set_checksum(message);
  return 0;         
}

int32_t get_xy_accel_message(dl1_message_t *message, float x_accel, float y_accel) {
  FAIL_ON_NULL(message);

  float tmp_x = x_accel;
  float tmp_y = y_accel;
    
  unsigned char x_b1 = 0;
  unsigned char x_b2 = 0;
  unsigned char y_b1 = 0;
  unsigned char y_b2 = 0;

  if (tmp_x > 0.0) { 
      x_b1 = 0x80;    
  } else {
    tmp_x *= -1;
  }

  if (tmp_y > 0.0) { 
      y_b1 = 0x80;    
  } else {
    tmp_y *= -1;
  }

  x_b1 |= (int)(tmp_x) & 0x7F;
  x_b2 =  (int)((tmp_x - (float)x_b1) * 0x100) & 0xFF;
  y_b1 |= (int)(tmp_y) & 0x7F;
  y_b2 =  (int)((tmp_y - (float)y_b1) * 0x100) & 0xFF;
    
  message->data[0] = XYACCEL_MESSAGE_ID;
  message->data[1] = x_b1; 
  message->data[2] = x_b2;
  message->data[3] = y_b1;
  message->data[4] = y_b2;
  message->length = 5;
  set_checksum(message);
  return 0;         
}

int32_t get_brake_pressure_message(dl1_message_t *message, uint16_t pressure_bar_x10) {
  FAIL_ON_NULL(message);

  int16_t voltage_x1000 = pressure_bar_x10 * 100 * 5 / MAX_BRAKE_PRESSURE_BAR;
  message->data[0] = TPS_MESSAGE_ID;
  message->data[1] = voltage_x1000 >> 8;
  message->data[2] = voltage_x1000;
  message->length = 3;
  set_checksum(message);
  return 0;       
}

/////////////////////////////////////////////////////////////////////////////
