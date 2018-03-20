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

GPS_REQUIRED_FIELDS = ['time', 'lat', 'lon', 'speed', 'track', 'epx', 'epy', 'epv', 'alt']
GPS_READ_TIMEOUT = 2.0


class GpsSensorHandler(SensorHandler):

    def __init__(self):
        SensorHandler.__init__(self, self.__record_from_gps)

    def __record_from_gps(self):
        # TODO auto retry and reinit on hotplug

        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        print("Starting GPS reader")
        gps_socket = gps3.GPSDSocket()
        data_stream = gps3.DataStream()
        gps_socket.connect()
        gps_socket.watch()
        while not self.doneEvent.is_set():
            newdata = gps_socket.next(timeout=GPS_READ_TIMEOUT)
            now = time.time()
            if newdata:
                data_stream.unpack(newdata)
                sample = data_stream.TPV
                t = sample.get('time')
                if t is not None and set(GPS_REQUIRED_FIELDS).issubset(set(sample.keys())):
                    self.pipe_out.send((now, sample))

        print("GPS reader shutdown")




    

