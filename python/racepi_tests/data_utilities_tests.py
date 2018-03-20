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
from collections import defaultdict
from unittest import TestCase, main

from racepi.sensor.data_utilities import TimeToDistanceConverter, \
    merge_and_generate_ordered_log, oversteer_coefficient


class TimeToDistanceConverterTest(TestCase):

    linear_speed_data = [
        (0.0, 1.0),
        (1.0, 1.0),
        (1.5, 1.0),
        (10.0, 1.0),
        (20.0, 1.0),
        (100.0, 1.0)
    ]

    def setUp(self):
        self.c = TimeToDistanceConverter(TimeToDistanceConverterTest.linear_speed_data)

    def test_time_to_distance_converter_no_data(self):
        self.assertRaises(ValueError, TimeToDistanceConverter, None)
        self.assertRaises(ValueError, TimeToDistanceConverter, [])

    def test_time_to_distance_converter_linear_speed(self):
        self.assertIsNotNone(self.c)
        # verify that speeds of 1.0 match time
        for d in self.c.distance_samples:
            self.assertAlmostEqual(d[0], d[1])

    def test_generate_distance_trace(self):
        trace = [
            1.2,
            30.5,
        ]
        result = self.c.generate_distance_trace(trace)
        # verify distance matches time
        for i in range(len(trace)):
            self.assertAlmostEqual(trace[i], result[i])


class OtherTests(TestCase):

    def test_merge_and_generate_ordered_log_empty(self):
        result = merge_and_generate_ordered_log(defaultdict(list))
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_merge_and_generate_ordered_log_single_entry(self):
        values = ["foo", "bar", None]
        times = [2, 1, 3]
        data = {"k": [(t, values) for t in times]}
        res = merge_and_generate_ordered_log(data)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0][1], 1)
        self.assertEqual(res[1][1], 2)
        self.assertEqual(res[2][1], 3)

    def test_merge_and_generate_ordered_log_interleaved(self):
        values1 = ["foo", "bar", None]
        values2 = ["stuff", "morestuff"]
        times1 = [2, 10, 30]
        times2 = [3, 9, 20]
        data = {"k": [(t, values1) for t in times1], "k2": [(t, values2) for t in times2]}
        res = merge_and_generate_ordered_log(data)
        self.assertEqual(len(res), 6)
        self.assertEqual(res[0][1], 2)
        self.assertEqual(res[1][1], 3)
        self.assertEqual(res[2][1], 9)
        self.assertEqual(res[3][1], 10)
        self.assertEqual(res[4][1], 20)
        self.assertEqual(res[5][1], 30)

    def test_oversteer_coefficient_zero_velocity(self):
        self.assertAlmostEqual(-1.0, oversteer_coefficient(1, 1, 0.0, 1), 6)
        self.assertAlmostEqual(-2.0, oversteer_coefficient(2, 2, 0.0, 2), 6)
        self.assertAlmostEqual(0.0, oversteer_coefficient(0, 0, 0.0, 0), 6)

if __name__ == "__main__":
    main()
