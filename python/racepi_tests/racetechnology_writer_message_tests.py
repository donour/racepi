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

    def test_get_z_accel_message_len(self):
        msg = get_z_accel_message_bytes(0)
        self.assertEqual(len(msg), 3)

    def test_get_z_accel_message_header(self):
        msg = get_z_accel_message_bytes(0)
        self.assertEqual(Z_ACCEL_MESSAGE_ID, msg[0])

    def test_get_z_accel_message_zero(self):
        msg = get_z_accel_message_bytes(0)
        self.assertEqual(0, msg[1])
        self.assertEqual(0, msg[2])

    def test_get_z_accel_message_positive(self):
        msg = get_z_accel_message_bytes(0.1)
        self.assertEqual(0x80, msg[1])

    def test_get_z_accel_message_negative(self):
        msg = get_z_accel_message_bytes(-0.1)
        self.assertEqual(0, msg[1])

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

    def test_get_tps_message_header(self):
        msg = get_tps_message_bytes(0)
        self.assertEqual(TPS_MESSAGE_ID, msg[0])

    def test_get_tps_message_length(self):
        msg = get_tps_message_bytes(0)
        self.assertEqual(3, len(msg))

    def test_get_tps_message_zero(self):
        msg = get_tps_message_bytes(0)
        self.assertEqual(0, msg[1])
        self.assertEqual(0, msg[2])

    def test_get_tps_message_5v(self):
        msg = get_tps_message_bytes(5.0)
        self.assertEqual(19, msg[1])
        self.assertEqual(136, msg[2])

    def test_get_steering_angle_message_header(self):
        msg = get_steering_angle_message_bytes(0)
        self.assertEqual(STEERING_ANGLE_ID, msg[0])
        self.assertEqual(0x3, msg[1])

    def test_get_steering_angle_message_length(self):
        msg = get_steering_angle_message_bytes(0)
        self.assertEqual(4, len(msg))

    def test_get_steering_angle_message_zero(self):
        msg = get_steering_angle_message_bytes(0)
        self.assertEqual(0, msg[2])
        self.assertEqual(0, msg[3])

    def test_get_steering_angle_message_90(self):
        msg = get_steering_angle_message_bytes(90)
        angle = (msg[2] + (msg[3] << 8)) / 10
        self.assertEqual(90, angle)

    def test_get_steering_angle_message_200(self):
        msg = get_steering_angle_message_bytes(200)
        angle = (msg[2] + (msg[3] << 8)) / 10
        self.assertEqual(200, angle)

    def test_get_steering_angle_message_720(self):
        msg = get_steering_angle_message_bytes(720)
        angle = (msg[2] + (msg[3] << 8)) / 10
        self.assertEqual(720, angle)

    def test_get_steering_angle_message_90_negative(self):
        msg = get_steering_angle_message_bytes(-90)
        angle = - (65536 - (msg[2] + (msg[3] << 8))) / 10
        self.assertEqual(-90, angle)

    def test_get_steering_angle_message_720_negative(self):
        msg = get_steering_angle_message_bytes(-720)
        angle = - (65536 - (msg[2] + (msg[3] << 8))) / 10
        self.assertEqual(-720, angle)

    def test_get_ext_pressure_message_header(self):
        msg = get_ext_pressure_message_bytes(0.0)
        self.assertEqual(EXT_PRESSURE_MESSAGE_ID, msg[0])
        self.assertEqual(1, msg[1])

    def test_get_ext_pressure_message_negative(self):
        msg = get_ext_pressure_message_bytes(-1.23)
        self.assertEqual(0, msg[2])
        self.assertEqual(0, msg[3])
        self.assertEqual(0, msg[4])

    def test_get_ext_pressure_message_zero(self):
        msg = get_ext_pressure_message_bytes(0.0)
        self.assertEqual(0, msg[2])
        self.assertEqual(0, msg[3])
        self.assertEqual(0, msg[4])

    def test_get_ext_pressure_message_small_pressure(self):
        msg = get_ext_pressure_message_bytes(1.0e-5)
        self.assertEqual(247, msg[2])
        self.assertEqual(16, msg[3])
        self.assertEqual(39, msg[4])

    def test_get_ext_pressure_message_unit_pressure(self):
        msg = get_ext_pressure_message_bytes(1.0)
        self.assertEqual(252, msg[2])
        self.assertEqual(16, msg[3])
        self.assertEqual(39, msg[4])

    def test_get_ext_pressure_message_moderate_pressure(self):
        msg = get_ext_pressure_message_bytes(12345)
        self.assertEqual(0, msg[2])
        self.assertEqual(57, msg[3])
        self.assertEqual(48, msg[4])

    def test_get_ext_pressure_message_big_pressure(self):
        msg = get_ext_pressure_message_bytes(12.34e46)
        self.assertEqual(43, msg[2])
        self.assertEqual(52, msg[3])
        self.assertEqual(48, msg[4])

    def test_get_brake_pressure_message_header(self):
        msg = get_brake_pressure_message_bytes(0.0)
        self.assertEqual(BRAKE_MESSAGE_ID, msg[0])

    def test_get_brake_pressure_message_length(self):
        msg = get_brake_pressure_message_bytes(0.0)
        self.assertEqual(3, len(msg))


if __name__ == "__main__":
    main()
