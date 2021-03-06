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
import os
import time

from racepi.sensor.handler.sensor_handler import SensorHandler

try:
    import RTIMU
except ImportError:
    RTIMU = None

SETTINGS_FILE = "/etc/RTIMULib.ini"


class RpiImuSensorHandler(SensorHandler):

    def __init__(self):
        SensorHandler.__init__(self, self.__record_from_imu)

    def __record_from_imu(self):
        """
        Record data entries from RaspberryPi SensorHat IMU to
        specified Queue
        """

        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        if not RTIMU:
            raise RuntimeError("No Pi HAT IMU modules available")
        
        os.system("taskset -p 0xfe %d" % os.getpid())
        os.nice(30)

        if not os.path.exists(SETTINGS_FILE):
            print("Settings file not found, creating file: " + SETTINGS_FILE)
        else:
            print("Loading settings: " + SETTINGS_FILE)
        _settings = RTIMU.Settings(SETTINGS_FILE)

        imu = RTIMU.RTIMU(_settings)

        print("IMU Name: " + imu.IMUName())

        if not imu.IMUInit():
            raise IOError("IMU init failed")

        imu.setSlerpPower(0.02)
        imu.setGyroEnable(True)
        imu.setAccelEnable(True)
        imu.setCompassEnable(True)
        poll_interval_ms = imu.IMUGetPollInterval()
        print("Poll Interval: %d (ms)" % poll_interval_ms)
        print("IMU Init Succeeded")
        while not self.doneEvent.is_set():
            if imu.IMURead():
                data = imu.getIMUData()
                self.pipe_out.send((time.time(), data))
                time.sleep(poll_interval_ms * 0.95 / 1000.0)

