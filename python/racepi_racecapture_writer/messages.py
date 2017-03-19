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

import struct

TIMESTAMP_MESSAGE_ID = 9
GPS_POS_MESSAGE_ID = 10
GPS_SPEED_MESSAGE_ID = 11

TIMESTAMP_FMT = ">4B"    # header, time
GPS_POS_FMT = "!BiiI"   # header, latitude, longitude, accuracy
GPS_SPEED_FMT = "!BII"  # header, speed, accuracy


def get_message_checksum(msg):
    cs = 0
    for d in msg:
        cs += d & 0xFF
    return bytes([cs & 0xFF])


def get_timestamp_message_bytes(time_millis):
    """
    :param time_millis: time since service start, in milliseconds
    :return:
    """
    # careful here, python3 ints are 64 bits wide when they need to be
    t = int(time_millis)
    t1 = (t>>16) & 0xFF
    t2 = (t>> 8) & 0xFF
    t3 = (t    ) & 0xFF
    return struct.pack(TIMESTAMP_FMT, TIMESTAMP_MESSAGE_ID, t1, t2, t3)


def get_gps_pos_message_bytes(gps_lat_xe7, gps_long_xe7):
    """
    :param gps_lat_xe7: latitude value, scaled by 1e7
    :param gps_long_xe7: longitude value, scale by 1e7
    :return:
    """
    return struct.pack(GPS_POS_FMT, GPS_POS_MESSAGE_ID, int(gps_lat_xe7), int(gps_long_xe7), 0)


def get_gps_speed_message_bytes(gps_speed_x100):
    """
    :param gps_speed_x100: speed (m/s), scaled by 100
    :return:
    """
    return struct.pack(GPS_SPEED_FMT, GPS_SPEED_MESSAGE_ID, int(gps_speed_x100), 0)
