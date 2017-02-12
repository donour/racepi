#!/usr/bin/env python3
# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

import time
import sys
import os
from racepi_sensor_handler.stn11xx import STNHandler

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: %s <CAN ID> <CAN ID> ..." % sys.argv[0])
        sys.exit(1)

    sh = STNHandler(DEV_NAME, BAUD_RATE)
    # setup monitor of specified IDs
    last_mesg = {}
    for can_id in sys.argv[1:]:
        last_mesg[can_id] = None
    sh.set_monitor_ids(last_mesg.keys())

    sh.start_monitor()
    last_update = 0
    while True:
        # read all the messages that are available
        data = sh.readline()
        if len(data) > 3:
            can_id = data[:3]
            if can_id in last_mesg.keys():
                last_mesg[can_id] = data

        now = time.time()
        if now - last_update > 0.2:
            last_update = now
            os.write(1, "\r")
            for k in last_mesg.keys():
                os.write(1, "[%s] " % last_mesg[k])
