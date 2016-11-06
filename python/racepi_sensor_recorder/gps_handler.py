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

import os
import gps
import time
from sensor_handler import SensorHandler

BAUD_RATE="38400"
GPS_REQUIRED_FIELDS = ['time','lat','lon','speed','track','epx','epy','epv']
DEFAULT_WAIT_FOR_NO_DATA=0.05

class GpsSensorHandler(SensorHandler):

    def __init__(self, gpsdev = '/dev/gps0'):
        SensorHandler.__init__(self, self.__record_from_gps)
        self.gpsdev = gpsdev

    def __record_from_gps(self):

        if not self.data_q:
            raise ValueError("Illegal argument, no queue specified")

        print("Starting GPS reader")
        session = gps.gps(mode = gps.WATCH_ENABLE)
        while not self.doneEvent.is_set():
            while not session:
                # set baudrate for serial gps receiver
                if os.path.isfile(gpsdev):
                    os.system("stty -F /dev/gpsm8n ispeed " + BAUD_RATE)
                    session = gps.gps(mode = gps.WATCH_ENABLE)
            
            data = session.next()
            t = data.get('time')
            if t is not None and set(GPS_REQUIRED_FIELDS).issubset(set(data.keys())):
                self.data_q.put( (time.time(), data))
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
            os.write(1, "\r" + str(data[0]))


    

