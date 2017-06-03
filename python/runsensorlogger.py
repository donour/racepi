#!/usr/bin/env python3
# Copyright 2016-7 Donour Sizemore
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
from racepi_sensor_handler.data_utilities import uptime_helper
from racepi_sensor_recorder import DbHandler, SensorLogger
from racepi_sensor_handler import GpsSensorHandler, RpiImuSensorHandler, GPS_REQUIRED_FIELDS, \
    STN11XXCanSensorHandler, SocketCanSensorHandler, LightSpeedTPMSSensorHandler

# TODO: move the DB filename to a config file in /etc
DEFAULT_SQLITE_FILE = '/external/racepi_data/test.db'
# TODO: make recorded can ids configurable
FORD_FOCUS_RS_CAN_IDS = [0x010, 0x070, 0x080, 0x090, 0x190, 0x213, 0x420]
ENDCOLOR  = '\033[0m'
UNDERLINE = '\033[4m'

if __name__ == "__main__":   
    import sys, time, logo  # display logo

    # delay startup while devices initialize
    while float(uptime_helper()) < 30.0:
        time.sleep(1)

    if len(sys.argv) < 2:
        dbfile = DEFAULT_SQLITE_FILE
    else:
        dbfile = sys.argv[1]

    print(UNDERLINE+"Starting RacePi Sensor Logger"+ENDCOLOR)

    print("Opening Sensor Handlers")
    handlers = {
        'gps': GpsSensorHandler(),
        'imu': RpiImuSensorHandler(),
        'can': SocketCanSensorHandler(can_filters=FORD_FOCUS_RS_CAN_IDS)
        # 'can': STN11XXCanSensorHandler(FORD_FOCUS_RS_CAN_IDS),
        # 'tpms': LightSpeedTPMSSensorHandler(),
    }

    print("Opening Database: %s" % dbfile)
    # TODO: look at opening DB as needed
    # to avoid corruption of tables
    db_handler = DbHandler(dbfile, GPS_REQUIRED_FIELDS)
    sl = SensorLogger(db_handler, handlers)
    sl.start()
