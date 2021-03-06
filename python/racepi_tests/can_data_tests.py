# Copyright 2016 Donour Sizemore
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

from unittest import TestCase

from racepi.can.data import CanFrameValueExtractor, CanFrame
from racepi.can import lotus_evora_s1_rpm_converter, \
    lotus_evora_s1_tps_converter, lotus_evora_s1_steering_angle_converter


class CanDataFrameTest(TestCase):

    def test_from_message_strings_None(self):
        with self.assertRaises(Exception):
            CanFrame(None, None)

    def test_from_message_strings_No_Id(self):
        with self.assertRaises(Exception):
            CanFrame(None, 'FFFFFFFFFFFFFFFF')

    def test_from_message_strings_No_Id2(self):
        with self.assertRaises(Exception):
            CanFrame(None, '00')

    def test_from_message_strings_short(self):
        f = CanFrame('000', '00')
        self.assertIsNotNone(f)
        self.assertEqual(len(f.arbId), 2)
        self.assertEqual(len(f.payload), 1)


class CanFrameValueExtractorTest(TestCase):

    def setUp(self):
        self.deadbeef = CanFrame('000', 'deadbeefdeadbeef')
        self.allbits  = CanFrame('000', 'ffffffffffffffff')
        self.nobits   = CanFrame('000', '0000000000000000')
        self.lastbit  = CanFrame('000', '0000000000000001')
        self.firstbit = CanFrame('000', '8000000000000000')
        self.zerotps  = CanFrame('080', '90007D00007FF3F7')
        self.fulltps  = CanFrame('080', '93E87D00007FF3F7')
        self.sdr      = CanFrame('010', '0229000080008036')
        self.sdl      = CanFrame('010', '0229000000008036')

        self.lotus_704_rpm        = CanFrame('400', '02C00000BAC000')
        self.lotus_zero_rpm       = CanFrame('400', '00000000BAC000')
        self.lotus_max_tps        = CanFrame('114', '000000FB000400')
        self.lotus_min_tps        = CanFrame('114', 'FFFFFF00FFFFFF')
        self.lotus_zero_steer     = CanFrame('085', '0000FFFFFFFFFF')
        self.lotus_negative_steer = CanFrame('085', 'FFFF0000000000')

    def test_init(self):
        self.assertIsNotNone(CanFrameValueExtractor(1, 2))

    def test_simple_convert(self):
        c = CanFrameValueExtractor(0, 64)

        v = c.convert_frame(CanFrame("000", "00"))
        self.assertEqual(v, 0)

        v = c.convert_frame(self.deadbeef)
        self.assertEqual(v, 0xdeadbeefdeadbeef)

    def test_simple_convert_floats(self):
        c = CanFrameValueExtractor(0, 64, a=1.0)
        v = c.convert_frame(self.deadbeef)
        self.assertTrue(abs(v - float(0xdeadbeefdeadbeef)) < 1e-19)

        c = CanFrameValueExtractor(0, 64, a=10.0)
        v = c.convert_frame(self.deadbeef)
        self.assertTrue(abs((v/float(0xdeadbeefdeadbeef) - 10.0)) < 1e-19)

    def test_first_bit(self):
        for i in range(0, 63):
            c = CanFrameValueExtractor(i, 1)
            self.assertEqual(c.convert_frame(self.firstbit), 1 if i == 0 else 0)

    def test_last_bit(self):
        for i in range(63):
            c = CanFrameValueExtractor(i, 1)
            self.assertEqual(c.convert_frame(self.lastbit), 1 if i == 63 else 0)

    def test_all_bits(self):
        c = CanFrameValueExtractor(0, 64)
        self.assertEqual(c.convert_frame(self.allbits), 0xffffffffffffffff)
        for i in range(63):
            c = CanFrameValueExtractor(i, 1)
            self.assertEqual(c.convert_frame(self.allbits), 1)

    def test_no_bits(self):
        c = CanFrameValueExtractor(0, 64)
        self.assertEqual(c.convert_frame(self.nobits), 0)
        for i in range(63):
            c = CanFrameValueExtractor(i, 1)
            self.assertEqual(c.convert_frame(self.nobits), 0)

    def test_simple_custom_transform(self):
        c = CanFrameValueExtractor(0, 64, custom_transform=lambda x: 0)
        self.assertEqual(c.convert_frame(self.deadbeef), 0)

        c = CanFrameValueExtractor(0, 64, custom_transform=lambda x: x-1)
        self.assertEqual(c.convert_frame(self.deadbeef), 0xdeadbeefdeadbeef - 1)

    def test_ford_tps(self):
        c = CanFrameValueExtractor(4, 12, a=0.1)
        self.assertTrue(abs(c.convert_frame(self.zerotps) - 0.0) < 1e-19)
        self.assertTrue(abs(c.convert_frame(self.fulltps)-100.0) < 1e-19)

    def test_ford_tps_offset(self):
        c = CanFrameValueExtractor(4, 12, a=0.1, c=-1000.0)
        self.assertTrue(abs(c.convert_frame(self.zerotps) + 1000.0) < 1e-19)
        self.assertTrue(abs(c.convert_frame(self.fulltps) + 900.0) < 1e-19)

    def test_ford_steering_direction_right(self):
        c = CanFrameValueExtractor(32, 1)
        self.assertNotEqual(0, c.convert_frame(self.sdr))

    def test_ford_steering_direction_left(self):
        c = CanFrameValueExtractor(32, 1)
        self.assertEqual(0, c.convert_frame(self.sdl))

    def test_lotus_evora_rpm_704(self):
        self.assertEqual(704, lotus_evora_s1_rpm_converter
                         .convert_frame(self.lotus_704_rpm))

    def test_lotus_evora_rpm_zero(self):
        self.assertEqual(0, lotus_evora_s1_rpm_converter
                         .convert_frame(self.lotus_zero_rpm))

    def test_lotus_evora_max_tps(self):
        self.assertEqual(100, lotus_evora_s1_tps_converter
                         .convert_frame(self.lotus_max_tps))

    def test_lotus_evora_min_tps(self):
        self.assertEqual(0, lotus_evora_s1_tps_converter
                         .convert_frame(self.lotus_min_tps))

    def test_lotus_evora_zero_steering(self):
        self.assertEqual(0, lotus_evora_s1_steering_angle_converter
                         .convert_frame(self.lotus_zero_steer))

    def test_lotus_evora_negative_one_steering(self):
        self.assertTrue(lotus_evora_s1_steering_angle_converter
                         .convert_frame(self.lotus_negative_steer) < 0)

