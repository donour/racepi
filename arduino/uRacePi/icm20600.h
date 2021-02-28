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

#ifndef __ICM_20600__
#define __ICM_20600__
#include <Wire.h>

class ICM20600 {

  private:
    const uint8_t addr = 0x68;
    TwoWire *i2c_dev;
    void writeByte(const uint8_t id, const uint8_t msg);
    uint8_t readByte(const uint8_t regAddr, unsigned char *data);
    int16_t readTwoByteSample(const uint8_t regAddrH, const uint8_t regAddrL);
    
  public:
    int8_t init(TwoWire *dev);

    float getXAccel();
    float getYAccel();
    float getZAccel();
};

#endif //__ICM_20600__
