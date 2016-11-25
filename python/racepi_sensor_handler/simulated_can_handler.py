#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
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

from sensor_handler import SensorHandler
import time

class SimulatedCanSensorHandler(SensorHandler):

    def __init__(self, msg_defs):
        """
        :param msg_defs: list of messages to generate,
            each should be a tuple of (msg_data, time_between_messages_millis)
        """
        SensorHandler.__init__(self, self.__generate_data)
        self.msg_defs = msg_defs

    def __generate_data(self):

        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        last_msg_times = {}
        for m in self.msg_defs:
            last_msg_times[m] = 0

        print("Starting SIMULATED CAN reader")
        while not self.doneEvent.is_set():
            now = time.time()*1000
            for m in self.msg_defs:
                if (last_msg_times[m] + m[1]) < now:
                    self.pipe_out.send((now, m[0]))
                    last_msg_times[m] = now
            time.sleep(0.001)

        print("Shutting down CAN reader")

if __name__ == "__main__":
    sh = SimulatedCanSensorHandler([("foo",500), ("bar",1000)])
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            print(data)
        else:
            time.sleep(0.1)