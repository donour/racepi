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
"""
Abtraction of RacePi's LED display interface
"""

import atexit, time
try:
    from sense_hat import SenseHat
except ImportError:
    SenseHat = None

IMU_COL = 0
GPS_COL = 1
CAN_COL = 2
BRIGHTNESS = 80
DISPLAY_UPDATE_TIME = 0.05
SENSOR_DISPLAY_TIMEOUT = 1.0


class RacePiStatusDisplay:
    """
    Helper class for displaying status information on the PiSenseHat LED matrix
    """

    def __init__(self, sense_hat=None):
        """
        Initialize display with SenseHat instance
        
        This clear the display and sets each sensor
        source to disconnected.

        """
        if not sense_hat:
            sense_hat = SenseHat()

        self.sense = sense_hat
        self.__clear()
        self.sense.set_rotation(90)
        atexit.register(self.__shutdown_mesg)

        self.set_col_lost(IMU_COL)
        self.set_col_lost(GPS_COL)
        self.set_col_lost(CAN_COL)
        self.last_heartbeat = time.time()
        self.heartbeat_active = False
        self.update_time = time.time()

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

    def refresh_display(self, gps_time=0, imu_time=0, can_time=0, recording=False):

        now = time.time()
        if now - self.update_time >  DISPLAY_UPDATE_TIME :

                if now - gps_time > SENSOR_DISPLAY_TIMEOUT:
                    self.set_col_init(GPS_COL)
                else:
                    self.set_col_ready(GPS_COL)

                if now - imu_time > SENSOR_DISPLAY_TIMEOUT:
                    self.set_col_init(IMU_COL)
                else:
                    self.set_col_ready(IMU_COL)

                if now - can_time > SENSOR_DISPLAY_TIMEOUT:
                    self.set_col_init(CAN_COL)
                else:
                    self.set_col_ready(CAN_COL)

                self.update_time = now
                self.heartbeat()
                self.set_recording_state(recording)

        
if __name__ == "__main__":

    s = RacePiStatusDisplay(SenseHat())
    s.set_col_lost(IMU_COL)
    s.set_col_init(GPS_COL)
    s.set_col_ready(CAN_COL)
    
    import time
    while True:
            time.sleep(1)
            s.set_recording_state(int(time.time()) % 2  == 0)
            s.heartbeat(3)
