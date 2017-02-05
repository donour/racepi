#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
"""
SensorHandler for CAN bus data. The handler records all messages
for a list of specified arbitration IDs. Messages are returned as
received, not decoded.
"""
import time

from serial.serialutil import SerialException

from sensor_handler import SensorHandler
from stn11xx import STNHandler


class STN11XXCanSensorHandler(SensorHandler):

    def __init__(self, can_ids=None):
        SensorHandler.__init__(self, self.__record_from_canbus)
        try:
            self.stn = STNHandler()
            self.stn.set_monitor_ids(can_ids)
        except SerialException:
            print("Failed to initialize CAN device")
            self.stn = None

    def __record_from_canbus(self):

        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        print("Starting CAN reader")
        if self.stn:
            self.stn.start_monitor()

            while not self.doneEvent.is_set():
                data = self.stn.readline()
                now = time.time()
                self.pipe_out.send((now, data))
                
            # stop monitors
            self.stn.stop_monitor()
        print("Shutting down CAN reader")

if __name__ == "__main__":
    sh = STN11XXCanSensorHandler()
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            print(data)
