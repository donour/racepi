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

import atexit

IMU_COL=0
GPS_COL=1
OBD_COL=2

BRIGHTNESS=80


class RacePiStatusDisplay:
    """
    Helper class for displaying status information on the PiSenseHat LED matrix
    """

    def __init__(self, senseHat):
        """
        Initialize display with SenseHat instance
        
        This clear the display and sets each sensor
        source to disconnected.

        """
        self.sense = senseHat
        self.__clear()
        self.sense.set_rotation(90)
        atexit.register(self.__shutdown_mesg)

        self.set_col_lost(IMU_COL)
        self.set_col_lost(GPS_COL)
        self.set_col_lost(OBD_COL)
        self.last_heartbeat = time.time()
        self.heartbeat_active = False

    def __shutdown_mesg(self):
        self.sense.show_message(".");
        
    def __clear(self):
        self.sense.clear()

    def set_col_lost(self, colNumber):
        """
        Set specified column to lost/disconnected

        colNumber should be one of the globally specified 
        column numbers.
        """
        self.sense.set_pixel(0, colNumber, BRIGHTNESS, 0, 0)
        self.sense.set_pixel(1, colNumber, 0, 0, 0)
        self.sense.set_pixel(2, colNumber, 0, 0, 0)

    def set_col_init(self, colNumber):
        """
        Set specified column to initializing/setup

        colNumber should be one of the globally specified 
        column numbers.
        """
        self.sense.set_pixel(0, colNumber, int(BRIGHTNESS*0.8), int(BRIGHTNESS*0.85), 0)
        self.sense.set_pixel(1, colNumber, int(BRIGHTNESS*0.8), int(BRIGHTNESS*0.85), 0)
        self.sense.set_pixel(2, colNumber, 0, 0, 0)


    def set_col_ready(self, colNumber):
        """
        Set specified column to ready/connected

        colNumber should be one of the globally specified 
        column numbers.
        """
        self.sense.set_pixel(0, colNumber, 0, BRIGHTNESS, 0)
        self.sense.set_pixel(1, colNumber, 0, BRIGHTNESS, 0)
        self.sense.set_pixel(2, colNumber, 0, BRIGHTNESS, 0)


    def set_recording_state(self, state):
        """
        Set recording state, True/False
        """
        for i in range(8):
            self.sense.set_pixel(7, i, 0 if state else BRIGHTNESS, BRIGHTNESS if state else 0, 0)

    def heartbeat(self, frequency = 1):
        now = time.time()
        if now - self.last_heartbeat > frequency:
            self.sense.set_pixel(0, 7,
                                 BRIGHTNESS if not self.heartbeat_active else 0,
                                 BRIGHTNESS if self.heartbeat_active else 0,
                                 0)
            self.last_heartbeat = now
            self.heartbeat_active = not self.heartbeat_active
    

if __name__ == "__main__":

    from sense_hat import SenseHat
    s = RacePiStatusDisplay(SenseHat())
    s.set_col_lost(IMU_COL)
    s.set_col_init(GPS_COL)
    s.set_col_ready(OBD_COL)
    
    import time
    while True:
            time.sleep(1)
            s.set_recording_state(int(time.time()) % 2  == 0)
            s.heartbeat(3)
