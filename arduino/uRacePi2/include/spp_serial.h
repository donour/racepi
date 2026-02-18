/**************************************************************************
    Copyright 2025 Donour Sizemore

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

#ifndef __SPP_SERIAL_H_
#define __SPP_SERIAL_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

void spp_serial_init(const char *device_name);
void spp_serial_write(const uint8_t *data, size_t len);
void spp_serial_printf(const char *fmt, ...);
int  spp_serial_available();
int  spp_serial_read();
bool spp_serial_connected();

#endif // __SPP_SERIAL_H_
