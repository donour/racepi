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
"""
Abstraction of RacePi's LED display interface
"""

import atexit
import time
from colorsys import hsv_to_rgb
from math import pi

try:
    from sense_hat import SenseHat
except ImportError:
    print("No Pi Sense Hat hardware found")
    SenseHat = None

DB_COL = 0
IMU_COL = 1
GPS_COL = 2
CAN_COL = 3
BRIGHTNESS = 80
DISPLAY_UPDATE_TIME = 0.05  # 20 hz
SENSOR_DISPLAY_TIMEOUT = 1.0
TIRE_DISPLAY_TIMEOUT = 8.0


class RacePiHatDisplayMissingError(RuntimeError):
    """Failed to detect PiHat hardware"""
    pass


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
            try: 
                sense_hat = SenseHat()
            except OSError as ex:
                raise RacePiHatDisplayMissingError from ex
            
        self.sense = sense_hat
        self.__clear()
        self.sense.set_rotation(90)
        atexit.register(self.__shutdown_mesg)

        self.set_col_lost(IMU_COL)
        self.set_col_lost(GPS_COL)
        self.set_col_lost(CAN_COL)
        self.last_heartbeat = time.time()
        self.heartbeat_active = False
        self.undervolt = False
        self.update_time = time.time()
        self.sense.show_message("PORSCHE", 0.005);
        
    def __shutdown_mesg(self) -> None:
        self.sense.show_message("cayman!", 0.005);
        
    def __clear(self):
        self.sense.clear()

    def set_col_lost(self, col_number):
        """
        Set specified column to lost/disconnected

        :param col_number: one of the globally specified column numbers
        :return: None
        """
        self.sense.set_pixel(0, col_number, BRIGHTNESS, 0, 0)
        self.sense.set_pixel(1, col_number, 0, 0, 0)
        self.sense.set_pixel(2, col_number, 0, 0, 0)

    def set_col_init(self, col_number):
        """
        Set specified column to initializing/setup

        :param col_number: one of the globally specified column numbers
        :return: None
        """
        self.sense.set_pixel(0, col_number, int(BRIGHTNESS*0.8), int(BRIGHTNESS*0.85), 0)
        self.sense.set_pixel(1, col_number, int(BRIGHTNESS*0.8), int(BRIGHTNESS*0.85), 0)
        self.sense.set_pixel(2, col_number, 0, 0, 0)

    def set_col_ready(self, col_number):
        """
        Set specified column to ready/connected

        :param col_number: one of the globally specified column numbers
        :return: None
        """
        self.sense.set_pixel(0, col_number, 0, BRIGHTNESS, 0)
        self.sense.set_pixel(1, col_number, 0, BRIGHTNESS, 0)
        self.sense.set_pixel(2, col_number, 0, BRIGHTNESS, 0)

    def set_recording_state(self, state):
        """
        Set recording state

        :param state: boolean
        :return: None
        """
        for i in range(8):
            self.sense.set_pixel(7, i, 0 if state else BRIGHTNESS, BRIGHTNESS if state else 0, 0)

    
    def draw_undervolt(self):
        """Draw undervolt indicator if set"""
        if self.undervolt:
            v = (BRIGHTNESS, 0, 0)
            for i in range(8):
                self.sense.set_pixel(i, i, v)
                self.sense.set_pixel(7-i, i, v)

    def set_undervolt(self):
        """Set undervolt condition sticky bit. This cannot be unset."""
        self.undervolt = True


    def heartbeat_color(self) -> int:
        i = 0
        while True:
            i = (i+1) % 255
            yield i
        
    def heartbeat(self, now, frequency=0.5):
        """
        Draw heartbeat indicator if necessary

        :param now: current time as float in seconds
        :param frequency: frequency to heartbeat, in hz
        :return: None
        """

        interval = 2*pi / 32    
        steps = 200/interval
        offset = (now - now/steps)
        
        for i in range(0,4):
            rgb1 = hsv_to_rgb(interval*i + offset, 1, BRIGHTNESS)
            v = [int(x) for x in rgb1]
            self.sense.set_pixel(6, i, v)
            self.sense.set_pixel(6, 7-i, v)
            self.sense.set_pixel(5, i, v)
            self.sense.set_pixel(5, 7-i, v)
            
        self.last_heartbeat = now
        self.heartbeat_active = not self.heartbeat_active

    def refresh_display(self, db_time=0, gps_time=0, imu_time=0, can_time=0, recording=False):
        """
        Refresh and redraw required display elements. All times floats in seconds.

        :param db_time:   time since last database access
        :param gps_time:  time since last gps sample
        :param imu_time:  time since last imu sample
        :param can_time:  time since last can bus sample
        :param tire_time: time since last tire pressure sample
        :param recording: boolean state of data recording
        :return:
        """
        now = time.time()
        if now - self.update_time > DISPLAY_UPDATE_TIME:

                if now - db_time > SENSOR_DISPLAY_TIMEOUT:
                    self.set_col_lost(DB_COL)
                else:
                    self.set_col_ready(DB_COL)
            
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
                self.set_recording_state(recording)
                self.heartbeat(now)
                self.draw_undervolt()

if __name__ == "__main__":
    if SenseHat:
        s = RacePiStatusDisplay(SenseHat())
        s.set_col_lost(DB_COL)
        s.set_col_lost(IMU_COL)
        s.set_col_init(GPS_COL)
        s.set_col_ready(CAN_COL)
        while True:
            time.sleep(1)
            s.set_recording_state(int(time.time()) % 2 == 0)
            s.heartbeat(time.time(), 3)
