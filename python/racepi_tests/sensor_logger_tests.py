#!/usr/bin/env python3
# Copyright 2016-7 Donour Sizemore
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
from racepi_sensor_recorder.sensor_log import SensorLogger, LoggerState, \
    MOVEMENT_THRESHOLD_M_PER_S, ACTIVATE_RECORDING_M_PER_S

TEST_COUNT = 10


class SensorLoggerTests(TestCase):

    def setUp(self):
        self.sl = SensorLogger(None)

    def test_safe_speed_to_float_none(self):
        v = self.sl.safe_speed_to_float(None)
        self.assertLess(v, 1e-10)

    def test_safe_speed_to_float_float(self):
        v1 = 123.456
        v2 = self.sl.safe_speed_to_float(v1)
        self.assertAlmostEqual(v1, v2, 3)

    def test_safe_speed_to_float_int(self):
        v1 = 123
        v2 = self.sl.safe_speed_to_float(v1)
        self.assertAlmostEqual(v1, v2, 3)

    def test_safe_speed_to_float_intstr(self):
        v1 = "123"
        v2 = self.sl.safe_speed_to_float(v1)
        self.assertAlmostEqual(123, v2, 3)

    def test_safe_speed_to_float_floatstr(self):
        v1 = "123.456"
        v2 = self.sl.safe_speed_to_float(v1)
        self.assertAlmostEqual(123.456, v2, 3)

    def test_safe_speed_to_float_badstr(self):
        v1 = "not number"
        v2 = self.sl.safe_speed_to_float(v1)
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

    def test_activate_conditions_empty(self):
        self.sl.db_handler = RuntimeError("no handler")  # TODO: mock this
        self.assertFalse(self.sl.activate_conditions(None))
        self.assertFalse(self.sl.activate_conditions({}))

    def test_activate_conditions_too_slow(self):
        self.sl.db_handler = RuntimeError("no handler")  # TODO: mock this
        samples = []
        data = {'gps': samples}
        self.assertFalse(self.sl.activate_conditions(data))
        samples.append((0, {'speed': ACTIVATE_RECORDING_M_PER_S-1e-10}))
        self.assertFalse(self.sl.activate_conditions(data))
        samples.insert(0, (0, {'speed': ACTIVATE_RECORDING_M_PER_S-1e-10}))
        self.assertFalse(self.sl.activate_conditions(data))

    def test_activate_conditions_true(self):
        self.sl.db_handler = RuntimeError("no handler")  # TODO: mock this
        samples = []
        data = {'gps': samples}
        samples.append((0, {'speed': ACTIVATE_RECORDING_M_PER_S+1e-10}))
        self.assertTrue(self.sl.activate_conditions(data))
        samples.append((0, {'speed': 0}))
        self.assertTrue(self.sl.activate_conditions(data))
        samples.insert(0, (0, {'speed': 0}))
        self.assertTrue(self.sl.activate_conditions(data))

    def test_deactivate_conditions_empty(self):
        self.assertFalse(self.sl.activate_conditions(None))
        self.assertFalse(self.sl.deactivate_conditions(None))
        self.assertFalse(self.sl.deactivate_conditions({}))

    def test_deactivate_conditions_false(self):
        self.sl.db_handler = RuntimeError("no handler")  # TODO: mock this
        samples = []
        data = {'gps': samples}
        samples.append((0, {'speed': MOVEMENT_THRESHOLD_M_PER_S+1e-10}))
        self.assertFalse(self.sl.deactivate_conditions(data))
        samples.append((0, {'speed': 0}))
        self.assertFalse(self.sl.deactivate_conditions(data))
        samples.insert(0, (0, {'speed': 0}))
        self.assertFalse(self.sl.deactivate_conditions(data))

    def test_deactivate_conditions_true(self):
        self.sl.db_handler = RuntimeError("no handler")  # TODO: mock this
        samples = []
        data = {'gps': samples}
        samples.append((0, {'speed': MOVEMENT_THRESHOLD_M_PER_S-1e-10}))
        self.assertTrue(self.sl.deactivate_conditions(data))
        samples.append((0, {'speed': 0}))
        self.assertTrue(self.sl.deactivate_conditions(data))
        samples.insert(0, (0, {'speed': 0}))
        self.assertTrue(self.sl.deactivate_conditions(data))

