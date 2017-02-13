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
from racepi_sensor_recorder.sensor_log \
    import DataBuffer, SensorLogger, LoggerState, safe_speed_to_float

TEST_COUNT = 10


class DataBufferTests(TestCase):

    def setUp(self):
        self.sl = SensorLogger(None)
        self.b = DataBuffer()
        self.twenty_samples = DataBuffer()
        for i in range(TEST_COUNT):
            self.twenty_samples.add_sample('one', [(i, 'data')])
            self.twenty_samples.add_sample('two', [(i, 'data')])

    def test_expire_old_samples_empty(self):
        self.b.expire_old_samples(0)
        self.assertEqual(len(self.b.data), 0)

    def test_get_available_sources_empty(self):
        self.assertListEqual(self.b.get_available_sources(), [])

    def test_get_sensor_data_empty(self):
        self.assertRaises(ValueError, self.b.get_sensor_data, "nosource")

    def test_add_samples(self):
        self.assertEqual(TEST_COUNT, len(self.twenty_samples.get_sensor_data('one')))
        self.assertEqual(TEST_COUNT, len(self.twenty_samples.get_sensor_data('two')))
        self.assertRaises(ValueError, self.twenty_samples.get_sensor_data, "nosource")

    def test_expire_old_samples_none(self):
        self.twenty_samples.expire_old_samples(0)
        self.assertEqual(TEST_COUNT, len(self.twenty_samples.get_sensor_data('one')))
        self.assertEqual(TEST_COUNT, len(self.twenty_samples.get_sensor_data('two')))
        self.assertRaises(ValueError, self.twenty_samples.get_sensor_data, "nosource")

    def test_expire_old_samples_one(self):
        self.twenty_samples.expire_old_samples(1)
        self.assertEqual(TEST_COUNT-1, len(self.twenty_samples.get_sensor_data('one')))
        self.assertEqual(TEST_COUNT-1, len(self.twenty_samples.get_sensor_data('two')))
        self.assertRaises(ValueError, self.twenty_samples.get_sensor_data, "nosource")

    def test_expire_old_samples_two(self):
        self.twenty_samples.expire_old_samples(2)
        self.assertEqual(TEST_COUNT-2, len(self.twenty_samples.get_sensor_data('one')))
        self.assertEqual(TEST_COUNT-2, len(self.twenty_samples.get_sensor_data('two')))
        self.assertRaises(ValueError, self.twenty_samples.get_sensor_data, "nosource")

    def test_expire_old_samples_all(self):
        self.twenty_samples.expire_old_samples(TEST_COUNT+1)
        self.assertEqual(0, len(self.twenty_samples.get_sensor_data('one')))
        self.assertEqual(0, len(self.twenty_samples.get_sensor_data('two')))
        self.assertRaises(ValueError, self.twenty_samples.get_sensor_data, "nosource")

    def test_safe_speed_to_float_none(self):
        v = safe_speed_to_float(None)
        self.assertLess(v, 1e-10)

    def test_safe_speed_to_float_float(self):
        v1 = 123.456
        v2 = safe_speed_to_float(v1)
        self.assertAlmostEqual(v1, v2, 3)

    def test_safe_speed_to_float_int(self):
        v1 = 123
        v2 = safe_speed_to_float(v1)
        self.assertAlmostEqual(v1, v2, 3)

    def test_safe_speed_to_float_intstr(self):
        v1 = "123"
        v2 = safe_speed_to_float(v1)
        self.assertAlmostEqual(123, v2, 3)

    def test_safe_speed_to_float_floatstr(self):
        v1 = "123.456"
        v2 = safe_speed_to_float(v1)
        self.assertAlmostEqual(123.456, v2, 3)

    def test_safe_speed_to_float_badstr(self):
        v1 = "not number"
        v2 = safe_speed_to_float(v1)
        self.assertLess(v2, 1e-10)

    def test_process_new_data_none(self):
        # This should never through an exception
        self.sl.process_new_data(None)

    def test_process_new_data_empty_completes(self):
        # This should never through an exception
        self.sl.process_new_data({})

    def test_process_new_data_empty_keeps_state(self):
        # This should never through an exception
        for s in LoggerState:
            self.sl.state = s
            try:
                self.sl.process_new_data({"empty": []})
            except RuntimeError:
                pass  # ignore invalid states
            self.assertEqual(self.sl.state, s, "Logger changed state")

