#!/usr/bin/env python2
import os, time
import RTIMU

SETTINGS_FILE = "/etc/RTIMULib.ini"
if not os.path.exists(SETTINGS_FILE):
    print("Settings file not found, creating file: " + SETTINGS_FILE)
else:
    print("Loading settings: " + SETTINGS_FILE)
_settings = RTIMU.Settings(SETTINGS_FILE)

_IMU = RTIMU.RTIMU(_settings)

print("IMU Name: " + _IMU.IMUName())

if not _IMU.IMUInit():
    raise IOError("IMU init failed")

_IMU.setSlerpPower(0.02)
_IMU.setGyroEnable(True)
_IMU.setAccelEnable(True)
_IMU.setCompassEnable(True)
_poll_interval = _IMU.IMUGetPollInterval()
print("Poll Interval: %d (ms)" % _poll_interval)
print("IMU Init Succeeded")

def record_from_imu(q, done):
    """
    Record data entries from RaspberryPi SensorHat IMU to
    specified Queue
    :param q: multiprocessor or thread Queue
    :param done: multiprocessor or thread Event, specifying recording complete
    :return: (time, IMU data sample) tuple
    """

    if not q:
        raise ValueError("Illegal argument, no queue specified")

    while not done.is_set():
        if _IMU.IMURead():
            data = _IMU.getIMUData()
            q.put((time.time(), data))
            time.sleep(_poll_interval * 0.5 / 1000.0)
        


