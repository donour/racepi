#!/usr/bin/env python2
import os, time
import RTIMU
from sensor_handler import SensorHandler

class RpiImuSensorHandler(SensorHandler):

    def __init__(self):
        SensorHandler.__init__(self, self.__record_from_imu)

    def __record_from_imu(self):
        """
        Record data entries from RaspberryPi SensorHat IMU to
        specified Queue
        """

        if not self.data_q:
            raise ValueError("Illegal argument, no queue specified")

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

        while not self.doneEvent.is_set():
            if _IMU.IMURead():
                data = _IMU.getIMUData()
                self.data_q.put((time.time(), data))
                time.sleep(_poll_interval * 0.5 / 1000.0)


if __name__ == "__main__":

    sh = RpiImuSensorHandler()
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            s = data[0][1]
            os.write(1, "\r" +
                 "[% 1.2f,% 1.2f,% 1.2f % 1.2f] : " % s.get('fusionQPose') +
                 "[% 1.2f,% 1.2f,% 1.2f] : " % s.get('fusionPose') +
                 "[% 1.2f,% 1.2f,% 1.2f] : " % s.get('accel') +
                 "[% 1.2f,% 1.2f,% 1.2f]" % s.get('gyro'))
