#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

import logo  # display logo
import racepi_sensor_recorder
from racepi_sensor_handler import GpsSensorHandler, RpiImuSensorHandler, CanSensorHandler

SQLITE_FILE = '/external/racepi_data/test.db'
# TODO: make recorded can ids configurable
FORD_FOCUS_RS_CAN_IDS = ["010", "070", "080", "090", "213", "420"]
ENDCOLOR  = '\033[0m'
UNDERLINE = '\033[4m'

print(UNDERLINE+"Starting RacePi Sensor Logger"+ENDCOLOR)

handlers = {
    'gps': GpsSensorHandler(),
    'imu': RpiImuSensorHandler(),
    'can': CanSensorHandler([])
}
sl = racepi_sensor_recorder.SensorLogger(SQLITE_FILE, handlers)
sl.start()
