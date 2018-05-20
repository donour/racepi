# Copyright 2018 Donour Sizemore
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
import os

from racepi.sensor.handler.sensor_handler import SensorHandler
from racepi.sensor.handler.stn11xx import STNHandler


class STN11XXOBD2SensorHandler(SensorHandler):

    def __init__(self, tty):
        SensorHandler.__init__(self, self.__poll_obd2_pids)
        self.stn = STNHandler(dev=tty, headers=False)

    def get_tps(self):
        rv = self.stn.get_pid("01", "11")

        if not rv or len(rv) < 6:
            return None  # insufficient response
        if "4111" not in rv[-6:-2]:
            return None  # invalid response

        tps_val = int(int(rv[-2:], 16) * 100 / 255)
        return tps_val

    def __poll_obd2_pids(self):
        """
        Get data from OBD2 pids. Currently this only supports Throttle Position
        :return:
        """
        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        os.system("taskset -p 0xfe %d" % os.getpid())
        os.nice(30)

        print("Starting OBD2 reader")
        while not self.doneEvent.is_set():

            tps = self.get_tps()
            if not tps:
                time.sleep(0.05)
            else:
                now = time.time()
                self.pipe_out.send((now, tps))

        print("Shutting down OBD2 reader")


if __name__ == "__main__":
    h = STN11XXOBD2SensorHandler("/dev/pts/2")
    h.start()
    while True:
        data = h.get_all_data()
        if data:
            print(data)
