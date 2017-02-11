#!/usr/bin/env python2
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
import racepi_sensor_recorder.sqlite_handler as slh


class DbHandlerTests(TestCase):

    def setUp(self):
        pass

    def test_uptime_helper(self):
        v = slh.uptime_helper()
        self.assertIsNotNone(v, "System uptime must be numeric value")
        self.assertGreater(v, 0, "System uptime must be greater than zero")
