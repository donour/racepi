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
#include "racepi_gnss.h"

#define UART_RX_PIN (16)
#define UART_TX_PIN (17)

const unsigned char I2C_UBX[] PROGMEM = 
  {0x06,0x00,0x14,0x00,0x00,0x00,0x00,0x00,0x84,0x00,
   0x00,0x00,0x00,0x00,0x00,0x00,0x07,0x00,0x01,0x00,
   0x00,0x00,0x00,0x00};
const unsigned char UART1_115200[] PROGMEM = 
  {0x06,0x00,0x14,0x00,0x01,0x00,0x00,0x00,0xC0,0x08,
   0x00,0x00,0x00,0xC2,0x01,0x00,0x07,0x00,0x03,0x00,
   0x00,0x00,0x00,0x00};

const unsigned char NAV_MODE[] PROGMEM = 
  {0x06,0x24,0x24,0x00,0xFF,0xFF,0x04,0x03,0x00,0x00,
   0x00,0x00,0x10,0x27,0x00,0x00,0x05,0x00,0xFA,0x00,
   0xFA,0x00,0x64,0x00,0x5E,0x01,0x00,0x3C,0x00,0x00,
   0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00};

const unsigned char RATE_64MS[] PROGMEM = 
  {0x06,0x08,0x06,0x00,0x40,0x00,0x01,0x00,0x01,0x00};

void sendUBX(HardwareSerial &port, const unsigned char *message, const int len )
{
  port.write(0xB5);port.write(0x62);
  uint8_t checksum[] = {0, 0};
  for (int i = 0; i < len; i++) {
    uint8_t c = message[i];
    checksum[0] += c;
    checksum[1] += checksum[0];
    port.write(c);     
  }
  port.write(checksum,2);
  port.flush();
}

int16_t setup_ublox_gnss(HardwareSerial &port) {

  // attempt slow startup for devices that default to factory baudrates
  port.begin(9600, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  sendUBX(port, UART1_115200, sizeof(UART1_115200));
  delay(200);
  
  port.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  delay(100);
  sendUBX(port, NAV_MODE, sizeof(NAV_MODE)); 
  delay(100);
  sendUBX(port, I2C_UBX, sizeof(I2C_UBX));
  delay(100);
  sendUBX(port, RATE_64MS, sizeof(RATE_64MS)); 
  return 0;
}
