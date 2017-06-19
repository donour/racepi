# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

from racepi_racetechnology_writer.writers import *
import time
from random import random


if __name__ == "__main__":

    writer = RaceTechnologyDL1FeedWriter()
    t0 = time.time()
    while True:
        t = time.time() - t0

        writer.send_timestamp(t)
        writer.send_gps_speed(int(random()*5))
        writer.send_gps_pos(72, 90)
        writer.send_steering_angle(int(random()*100))
        writer.send_xyz_accel(random(), random(), random())
        writer.send_tps(random()*100)
        writer.send_rpm(random()*5000)
        writer.send_brake_pressure(random()*100)
        writer.flush_queued_messages()
        time.sleep(0.2)

