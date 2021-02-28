/**************************************************************************
    Copyright 2021 Donour Sizemore

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
#include "icm20600.h"
#define ICM20600_CONFIG                 0x1a
#define ICM20600_FIFO_EN                0x23
#define ICM20600_GYRO_CONFIG            0x1b
#define ICM20600_ACCEL_CONFIG           0x1c
#define ICM20600_ACCEL_CONFIG2          0x1d
#define ICM20600_ACCEL_XOUT_H           0x3b
#define ICM20600_ACCEL_XOUT_L           0x3c
#define ICM20600_ACCEL_YOUT_H           0x3d
#define ICM20600_ACCEL_YOUT_L           0x3e
#define ICM20600_ACCEL_ZOUT_H           0x3f
#define ICM20600_ACCEL_ZOUT_L           0x40
#define ICM20600_PWR_MGMT_1             0x6b
#define ICM20600_PWR_MGMT_2             0x6c
#define ICM20600_FIFO_R_W               0x74
#define ICM20600_WHO_AM_I               0x75
#define ICM20600_XA_OFFSET_H            0x77
#define ICM20600_XA_OFFSET_L            0x78
#define ICM20600_YA_OFFSET_H            0x7a
#define ICM20600_YA_OFFSET_L            0x7b
#define ICM20600_ZA_OFFSET_H            0x7d
#define ICM20600_ZA_OFFSET_L            0x7e

#define TIMEOUT_MILLIS (250)
#define ICM_20600_ID (0x11)

void ICM20600::writeByte(const uint8_t id, const uint8_t msg) {
  i2c_dev->beginTransmission(addr);
  i2c_dev->write(id); 
  i2c_dev->write(msg);  
  i2c_dev->endTransmission();
}

uint8_t ICM20600::readByte(const uint8_t regAddr, unsigned char *data) {
  if (NULL == data) return -1;
  i2c_dev->beginTransmission(addr);
  i2c_dev->write(regAddr);
  i2c_dev->endTransmission();
  i2c_dev->beginTransmission(addr);
  i2c_dev->requestFrom(addr, (uint8_t) 1);
  
  // todo timeout
  uint64_t start = millis();

  while( ! i2c_dev->available() ) {            
    if ((millis() - start) > TIMEOUT_MILLIS) {
      -2;
    }
  }
  *data = i2c_dev->read();
  i2c_dev->endTransmission();

  return 0;
}

int16_t ICM20600::readTwoByteSample(const uint8_t regAddrH, const uint8_t regAddrL) {
   union {
    int16_t w;
    struct {
      unsigned char L;
      unsigned char H;
    };
  } value;
  readByte(regAddrH, &value.H);
  readByte(regAddrL, &value.L);
  return value.w;
}
    
int8_t ICM20600::init(TwoWire *dev) {
  unsigned char data;
  uint8_t rc;
  
  if (NULL == dev) { 
    return -1;
  }
  i2c_dev = dev;

  
  rc = readByte(ICM20600_WHO_AM_I, &data);
  if (rc != 0) {
    return -2;
  }
  if (data != ICM_20600_ID) {
    return -3;
  }
  
  writeByte(ICM20600_CONFIG, 0x00); 
  writeByte(ICM20600_FIFO_EN, 0x00); 

  // set low noise mode
  readByte(ICM20600_PWR_MGMT_1, &data);
  uint8_t pwr1 = data & 0x8f;
  uint8_t pwr2 = 0x07; // gyro disabled
  //uint8_t pwr2 = 0x00; // all axis enabled
  writeByte(ICM20600_PWR_MGMT_1, pwr1);
  writeByte(ICM20600_PWR_MGMT_2, pwr2);

  // set accel range
  readByte(ICM20600_ACCEL_CONFIG, &data);
  data &= 0xf0;
  writeByte(ICM20600_ACCEL_CONFIG, data);
  // set low pass filter
  readByte(ICM20600_ACCEL_CONFIG2, &data);
  data &= 0xf0;
  data |= 0x03;
  writeByte(ICM20600_ACCEL_CONFIG2, data);
  return 0;
}

float ICM20600::getXAccel() {
  return readTwoByteSample(ICM20600_ACCEL_XOUT_H, ICM20600_ACCEL_XOUT_L) / 16384.0;
}
float ICM20600::getYAccel() {
  return readTwoByteSample(ICM20600_ACCEL_YOUT_H, ICM20600_ACCEL_YOUT_L) / 16384.0;
}
float ICM20600::getZAccel() {
  return readTwoByteSample(ICM20600_ACCEL_ZOUT_H, ICM20600_ACCEL_ZOUT_L) / 16384.0;
}
