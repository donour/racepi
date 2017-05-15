#!/usr/bin/env python3
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

from unittest import TestCase

from racepi_sensor_handler.lightspeed_tpms_handler import LightSpeedTPMSMessageParser


class LightSpeedSensorHandlerTests(TestCase):

    def setUp(self):
        pass

    def test__parse_sample_none(self):
        self.assertIsNone(LightSpeedTPMSMessageParser._parse_data_sample(None))

    def test__parse_sample_wrong_size(self):
        self.assertIsNone(LightSpeedTPMSMessageParser._parse_data_sample(b'\x07'))
        self.assertIsNone(LightSpeedTPMSMessageParser._parse_data_sample(b'\x06'))
        self.assertIsNone(LightSpeedTPMSMessageParser._parse_data_sample(b'\x01'))
        self.assertIsNone(LightSpeedTPMSMessageParser._parse_data_sample(b'\xFF'))

    def test__parse_sample_location_lf(self):
        msg = b'\x08\x00\x00\x00\x00\x00'
        self.assertEqual('lf', LightSpeedTPMSMessageParser._parse_data_sample(msg)['location'])

    def test__parse_sample_location_rf(self):
        msg = b'\x08\x01\x00\x00\x00\x00'
        self.assertEqual('rf', LightSpeedTPMSMessageParser._parse_data_sample(msg)['location'])

    def test__parse_sample_location_lr(self):
        msg = b'\x08\x10\x00\x00\x00\x00'
        self.assertEqual('lr', LightSpeedTPMSMessageParser._parse_data_sample(msg)['location'])

    def test__parse_sample_location_rr(self):
        msg = b'\x08\x11\x00\x00\x00\x00'
        self.assertEqual('rr', LightSpeedTPMSMessageParser._parse_data_sample(msg)['location'])

    def test__parse_sample_temp_zero(self):
        msg = b'\x08\x01\x00\x32\x00\x00'
        self.assertEqual(0, LightSpeedTPMSMessageParser._parse_data_sample(msg)['temp'])

    def test__parse_sample_temp_100(self):
        msg = b'\x08\x01\x00\x96\x00\x00'
        self.assertEqual(100, LightSpeedTPMSMessageParser._parse_data_sample(msg)['temp'])

    def test__parse_sample_pressure_zero(self):
        msg = b'\x08\x01\x00\x32\x00\x00'
        self.assertEqual(0, LightSpeedTPMSMessageParser._parse_data_sample(msg)['pressure'])

    def test__parse_sample_pressure_2bar(self):
        msg = b'\x08\x01\x3A\x32\x00\x00'
        self.assertAlmostEqual(1.995, LightSpeedTPMSMessageParser._parse_data_sample(msg)['pressure'], 3)

    def test__parse_sample_low_voltage(self):
        msg = b'\x08\x01\x3A\x32\x00\x00'
        self.assertFalse(LightSpeedTPMSMessageParser._parse_data_sample(msg)['low_voltage'])
        msg = b'\x08\x01\x3A\x32\xEF\x00'
        self.assertFalse(LightSpeedTPMSMessageParser._parse_data_sample(msg)['low_voltage'])
        msg = b'\x08\x01\x3A\x32\xFF\x00'
        self.assertTrue(LightSpeedTPMSMessageParser._parse_data_sample(msg)['low_voltage'])
        msg = b'\x08\x01\x3A\x32\x10\x00'
        self.assertTrue(LightSpeedTPMSMessageParser._parse_data_sample(msg)['low_voltage'])

    def test__parse_sample_signal_loss(self):
        msg = b'\x08\x01\x3A\x32\x00\x00'
        self.assertFalse(LightSpeedTPMSMessageParser._parse_data_sample(msg)['signal_loss'])
        msg = b'\x08\x01\x3A\x32\xDF\x00'
        self.assertFalse(LightSpeedTPMSMessageParser._parse_data_sample(msg)['signal_loss'])
        msg = b'\x08\x01\x3A\x32\x20\x00'
        self.assertTrue(LightSpeedTPMSMessageParser._parse_data_sample(msg)['signal_loss'])
        msg = b'\x08\x01\x3A\x32\xFF\x00'
        self.assertTrue(LightSpeedTPMSMessageParser._parse_data_sample(msg)['signal_loss'])

    def test_unpack_messages(self):
        msg =       b'\x55\xAA\x08\x20\x00\x00\x00\x00'
        msg = msg + b'\x55\xAA\x08\x10\x00\x00\x00\x00'
        msg = msg + b'\x55\xAA\x08\x01\x00\x00\x00\x00'
        msg = msg + b'\x55\xAA\x08\x11\x00\x00\x00\x00'
        msg = msg + b'\x55\xAA\x08\x00\x00\x00\x00\x00'
        msg = msg + b'\x55\xAA\x08\x31\x00\x00\x00\x00'

        r = LightSpeedTPMSMessageParser.unpack_messages(msg)
        self.assertIsNotNone(r)
        for p in ['lf', 'rf', 'lr', 'rr']:
            self.assertIsNotNone(r.get(p))
