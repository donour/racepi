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

import time
from racepi.sensor.handler.lightspeed_tpms import LightSpeedTPMSSensorHandler

if __name__ == "__main__":
    sh = LightSpeedTPMSSensorHandler()
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            print(data)
        else:
            time.sleep(0.1)
