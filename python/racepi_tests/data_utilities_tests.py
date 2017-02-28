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

from racepi_sensor_handler.data_utilities import TimeToDistanceConverter


class TimeToDistanceConverterTest(TestCase):

    def test_time_to_distance_converter_no_data(self):
        self.assertRaises(ValueError, TimeToDistanceConverter, None)
        self.assertRaises(ValueError, TimeToDistanceConverter, [])

    def test_time_to_distance_converter_linear_speed(self):
        data = [
            (0.0, {'speed': 1.0}),
            (1.0, {'speed': 1.0}),
            (1.5, {'speed': 1.0}),
            (10.0, {'speed': 1.0}),
            (100.0, {'speed': 1.0})
        ]

        c = TimeToDistanceConverter(data)
        self.assertIsNotNone(c)

        # verify that speeds of 1.0 match time
        for d in c.distance_samples:
            self.assertAlmostEqual(d[0], d[1])
