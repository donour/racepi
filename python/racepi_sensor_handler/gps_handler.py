#!/usr/bin/env python3
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

import gps3.gps3 as gps3
import os
import time

from .sensor_handler import SensorHandler

GPS_REQUIRED_FIELDS = ['time', 'lat', 'lon', 'speed', 'track', 'epx', 'epy', 'epv']
DEFAULT_WAIT_FOR_NO_DATA = 0.05


class GpsSensorHandler(SensorHandler):

    def __init__(self, gpsdev='/dev/gps0'):
        SensorHandler.__init__(self, self.__record_from_gps)
        self.gpsdev = gpsdev

    def __record_from_gps(self):

        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        print("Starting GPS reader")
        gps_socket = gps3.GPSDSocket()
        data_stream = gps3.DataStream()
        gps_socket.connect()
        gps_socket.watch()
        while not self.doneEvent.is_set():
            newdata = gps_socket.next()
            now = time.time()
            if newdata:
                data_stream.unpack(newdata)
                sample = data_stream.TPV
                t = sample.get('time')
                if t is not None and set(GPS_REQUIRED_FIELDS).issubset(set(sample.keys())):
                    self.pipe_out.send((now, sample))
                else:
                    # relieve the CPU when getting unusable data
                    # 20hz is above the expected GPS sample rate
                    time.sleep(DEFAULT_WAIT_FOR_NO_DATA)

        print("GPS reader shutdown")
        
        
if __name__ == "__main__":

    sh = GpsSensorHandler()
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            os.write(1, ("\r" + str(data[0])).encode())

    

