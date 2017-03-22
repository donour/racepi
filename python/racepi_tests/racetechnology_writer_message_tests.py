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

from unittest import TestCase, main

from racepi_racetechnology_writer.messages import *


class RaceCaptureMessageTests(TestCase):

    def test_timestamp_message_header(self):
        msg = get_timestamp_message_bytes(0)
        self.assertEqual(TIMESTAMP_MESSAGE_ID, msg[0])

    def test_timestamp_message_length(self):
        msg = get_timestamp_message_bytes(0)
        self.assertEqual(len(msg), 4)

    def test_timestamp_message_contents(self):
        value = 0xDEADBEEF
        msg = get_timestamp_message_bytes(value)
        self.assertEqual(0xad, msg[1])
        self.assertEqual(0xbe, msg[2])
        self.assertEqual(0xef, msg[3])

    def test_gps_speed_message_header(self):
        msg = get_gps_speed_message_bytes(0)
        self.assertEqual(GPS_SPEED_MESSAGE_ID, msg[0])

    def test_gps_speed_message_length(self):
        msg = get_gps_speed_message_bytes(0)
        self.assertEqual(len(msg), 9)

    def test_gps_speed_message_contents(self):
        value = 0xDEADBEEF
        msg = get_gps_speed_message_bytes(value)
        self.assertEqual(0xde, msg[1])
        self.assertEqual(0xad, msg[2])
        self.assertEqual(0xbe, msg[3])
        self.assertEqual(0xef, msg[4])
        self.assertEqual(0, msg[5])
        self.assertEqual(0, msg[6])
        self.assertEqual(0, msg[7])
        self.assertEqual(0, msg[8])

    def test_gps_pos_message_header(self):
        msg = get_gps_pos_message_bytes(0, 0)
        self.assertEqual(GPS_POS_MESSAGE_ID, msg[0])

    def test_gps_pos_message_length(self):
        msg = get_gps_pos_message_bytes(0, 0)
        self.assertEqual(len(msg), 13)

    def test_gps_pos_message_positive(self):
        msg = get_gps_pos_message_bytes(89.9999, 179.999)
        self.assertEqual(len(msg), 13)

    def test_gps_pos_message_negative(self):
        msg = get_gps_pos_message_bytes(-89.9999, -179.999)
        self.assertEqual(len(msg), 13)

    def test_get_xy_accel_message_len(self):
        msg = get_xy_accel_message_bytes(0.0, 0.0)
        self.assertEqual(len(msg), 5)

    def test_get_xy_accel_message_header(self):
        msg = get_xy_accel_message_bytes(0.0, 0.0)
        self.assertEqual(XYACCEL_MESSAGE_ID, msg[0])

    def test_get_xy_accel_message_zero(self):
        msg = get_xy_accel_message_bytes(0.0, 0.0)
        self.assertEqual(0, msg[1])
        self.assertEqual(0, msg[2])
        self.assertEqual(0, msg[3])
        self.assertEqual(0, msg[4])

    def test_get_xy_accel_message_sign_positive(self):
        msg = get_xy_accel_message_bytes(0.1, 0.1)
        self.assertEqual(0x80, msg[1])
        self.assertEqual(0x80, msg[3])

    def test_get_xy_accel_message_sign_negative(self):
        msg = get_xy_accel_message_bytes(-0.1, -0.1)
        self.assertEqual(0, msg[1])
        self.assertEqual(0, msg[3])

    def test_get_message_checksum_zero(self):
        self.assertEqual(b'\x00', get_message_checksum(b'\x00'))
        self.assertEqual(b'\x00', get_message_checksum(b'\x00\x00'))
        self.assertEqual(b'\x00', get_message_checksum(b''))

    def test_get_message_checksum_single_byte(self):
        self.assertEqual(b'\xab', get_message_checksum(b'\xab'))

    def test_get_message_checksum_single_overflow(self):
        self.assertEqual(b'\x00', get_message_checksum(b'\xff\x01'))

    def test_get_rpm_message_header(self):
        msg = get_rpm_message_bytes(0)
        self.assertEqual(RPM_MESSAGE_ID, msg[0])

    def test_get_rpm_message_len(self):
        msg = get_rpm_message_bytes(0)
        self.assertEqual(len(msg), 4)

    def test_get_rpm_message_zero(self):
        msg = get_rpm_message_bytes(0)
        self.assertEqual(0, msg[1])
        self.assertEqual(0, msg[2])
        self.assertEqual(0, msg[3])

    def test_get_rpm_message_1000(self):
        msg = get_rpm_message_bytes(1000)
        self.assertEqual(5, msg[1])
        self.assertEqual(126, msg[2])
        self.assertEqual(64, msg[3])


if __name__ == "__main__":
    main()
