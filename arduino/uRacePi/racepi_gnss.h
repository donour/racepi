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

#ifndef __RACEPI_GNSS_
#define __RACEPI_GNSS_

#define GPS_FIX_SPD_ERR
#define GPS_FIX_LAT_ERR
#define LAST_SENTENCE_IN_INTERVAL NMEAGPS::NMEA_GLL

#include <HardwareSerial.h>
#include <NMEAGPS.h>
#include <Streamers.h>

static NMEAGPS gps;

int16_t setup_ublox_gnss(HardwareSerial &port);
 
#endif //__RACEPI_GNSS_
