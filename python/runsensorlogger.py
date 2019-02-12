#!/usr/bin/env python3
# Copyright 2016-8 Donour Sizemore
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

import os

from racepi.sensor.data_utilities import uptime_helper
from racepi.sensor.recorder.sensor_log import SensorLogger
from racepi.database.db_handler import DbHandler
from racepi.sensor.handler.gps import GpsSensorHandler
from racepi.sensor.handler.pi_sense_hat_imu import RpiImuSensorHandler
from racepi.sensor.handler.stn11xx_can import STN11XXCanSensorHandler

# TODO: move the DB filename to a config file in /etc
DEFAULT_SQLITE_FILE = '/external/racepi_data/test.db'
# TODO: make recorded can ids configurable
FORD_FOCUS_RS_CAN_IDS  = [0x010, 0x070, 0x080, 0x090, 0x190, 0x130, 0x213, 0x420]
LOTUS_EVORA_S1_CAN_IDS = [0x085, 0x114, 0x400]
ACTIVE_CAN_IDS = LOTUS_EVORA_S1_CAN_IDS
DBC_FILENAME = os.environ['HOME'] + "/git/racepi/dbc/evora.dbc"
ENDCOLOR  = '\033[0m'
UNDERLINE = '\033[4m'

if __name__ == "__main__":   
    import sys
    import time

    # delay startup while devices initialize
    while float(uptime_helper()) < 10.0:
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
        # 'can': SocketCanSensorHandler(can_filters=ACTIVE_CAN_IDS),
        'can': STN11XXCanSensorHandler(ACTIVE_CAN_IDS),
        # 'tpms': LightSpeedTPMSSensorHandler(),
    }

    print("Opening Database: %s" % dbfile)
    # TODO: look at opening DB as needed
    # to avoid corruption of tables
    db_handler = DbHandler(dbfile)
    sl = SensorLogger(db_handler, handlers, DBC_FILENAME)
    sl.start()
