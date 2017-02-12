#!/usr/bin/env python3
# Copyright 2017 Donour Sizemore
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

from pi_sense_hat_imu import RpiImuSensorHandler

if __name__ == "__main__":

    sh = RpiImuSensorHandler()
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            s = data[0][1]
            print(\
            "[% 1.2f,% 1.2f,% 1.2f % 1.2f] : " % s.get('fusionQPose') +
            "[% 1.2f,% 1.2f,% 1.2f] : " % s.get('fusionPose') +
            "[% 1.2f,% 1.2f,% 1.2f] : " % s.get('accel') +
            "[% 1.2f,% 1.2f,% 1.2f]" % s.get('gyro'))
