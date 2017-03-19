# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

import time
import serial
from .messages import *

RC_BAUD_RATE = 230400


class RaceCaptureFeedWriter:

    def __init__(self, output):
        dev = "/dev/rfcomm1"
        self.port = serial.Serial(dev, RC_BAUD_RATE)
        if dev != self.port.getPort():
            raise IOError("Could not open" + dev)

        self.output = output
        self.__test_file = open("/external/testfile", "wb")
        print("Writing RC testfile: /external/testfile")
        self.__earliest_time_seen = time.time()

    def __send_mesg(self, msg):
        # send message content
        self.__test_file.write(msg)
        self.port.write(msg)
        # send checksum
        self.__test_file.write(get_message_checksum(msg))
        self.port.write(get_message_checksum(msg))

    def send_timestamp(self, timestamp_seconds):
        if not timestamp_seconds:
            return

        time_delta = timestamp_seconds - self.__earliest_time_seen
        msg = get_timestamp_message_bytes(time_delta * 1000.0)
        self.__send_mesg(msg)

    def send_gps_speed(self, speed):
        if not speed:
            return

        msg = get_gps_speed_message_bytes(speed*100.0)
        self.__send_mesg(msg)

    def send_gps_pos(self, lat, lon):
        if not lat or not lon:
            return

        msg = get_gps_pos_message_bytes(float(lat) * float(1e7), float(lon) * float(1e7))
        self.__send_mesg(msg)
