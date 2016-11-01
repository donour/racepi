#!/usr/bin/env python2
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
from racepi_sensor_recorder.can_data import CanFrameValueExtractor, CanFrame


class CanDataFrameTest(TestCase):

    def test_from_message_strings_None(self):
        with self.assertRaises(ValueError):
            CanFrame(None, None)

    def test_from_message_strings_NoId(self):
        with self.assertRaises(ValueError):
            CanFrame(None, 'FFFFFFFFFFFFFFFF')

    def test_from_message_strings_NoId2(self):
        with self.assertRaises(ValueError):
            CanFrame(None, '00')

    def test_from_message_strings_short(self):
        f = CanFrame('000', '00')
        self.assertIsNotNone(f)
        self.assertEqual(len(f.arbId), 2)
        self.assertEqual(len(f.payload), 1)


class CanFrameValueExtractorTest(TestCase):

    def test_init(self):
        self.assertIsNotNone(CanFrameValueExtractor(1, 2))

    def test_simple_convert(self):
        c = CanFrameValueExtractor(0, 64)

        v = c.convert_frame(CanFrame("000", "00"))
        self.assertEqual(v, 0)

        v = c.convert_frame(CanFrame("000", "deadbeefdeadbeef"))
        self.assertEqual(v, 0xdeadbeefdeadbeef)

    def test_simple_convert_floats(self):

        c = CanFrameValueExtractor(0, 64, a=1.0)
        v = c.convert_frame(CanFrame("000", "deadbeefdeadbeef"))
        self.assertTrue(abs(v - float(0xdeadbeefdeadbeef)) < 1e-19)

        c = CanFrameValueExtractor(0, 64, a=10.0)
        v = c.convert_frame(CanFrame("000", "deadbeefdeadbeef"))
        self.assertTrue(abs(( v/float(0xdeadbeefdeadbeef) - 10.0)) < 1e-19)


