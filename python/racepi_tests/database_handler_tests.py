#!/usr/bin/env python3
# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

from unittest import TestCase
from racepi_database_handler import *
from racepi_database_handler.DbHandler import DbHandler
from uuid import UUID

TEST_DB_LOCATION = "testdata/test.db"


class DatabaseHandlerTest(TestCase):

    def setUp(self):
        self.h = DbHandler(TEST_DB_LOCATION)
        self.assertIsNotNone(self.h)
        self.h.connect()

    def test_init(self):
        prev_val = len(self.h.db_session.query(Session).all())
        session_id = self.h.get_new_session()
        self.assertIsNotNone(UUID(session_id))
        new_val = len(self.h.db_session.query(Session).all())
        self.assertEqual(prev_val+1, new_val)

    def test_insert_gps_samples(self):
        s = self.h.get_new_session()
        self.assertEqual(0,
                         len(self.h.db_session.query(GPSData).filter(GPSData.session_id == s).all()))
        data = {'time': "123.456", "speed": "12.34", "track": '300.0'}
        data = [(123.456, data)]
        self.h.insert_gps_updates(data, s)
        self.assertEqual(1,
                         len(self.h.db_session.query(GPSData).filter(GPSData.session_id == s).all()))

    def test_insert_imu_samples(self):
        s = self.h.get_new_session()
        self.assertEqual(0,
                         len(self.h.db_session.query(IMUData).filter(IMUData.session_id == s).all()))
        data = {'fusionPose': [1, 2, 3], 'accel': [1, 2, 3], 'gyro': [1, 2, 3]}
        data = [(123.45, data)]
        self.h.insert_imu_updates(data, s)
        self.assertEqual(1,
                         len(self.h.db_session.query(IMUData).filter(IMUData.session_id == s).all()))

    def test_insert_can_samples(self):
        s = self.h.get_new_session()
        self.assertEqual(0,
                         len(self.h.db_session.query(CANData).filter(CANData.session_id == s).all()))
        data = "010DEADBEEF"
        data = [(123.45, data)]
        self.h.insert_can_updates(data, s)
        self.assertEqual(1,
                         len(self.h.db_session.query(CANData).filter(CANData.session_id == s).all()))

    def test_insert_tpms_samples(self):
        s = self.h.get_new_session()
        self.assertEqual(0,
                         len(self.h.db_session.query(TireData).filter(TireData.session_id == s).all()))
        data = {
            'lf': {'pressure': 123, 'temp': 34},
            'rf': {'pressure': 123, 'temp': 34},
            'lr': {'pressure': 123, 'temp': 34},
            'rr': {'pressure': 123, 'temp': 34}
        }
        data = [(123.45, data)]
        self.h.insert_tpms_updates(data, s)
        self.assertEqual(1,
                         len(self.h.db_session.query(TireData).filter(TireData.session_id == s).all()))

    def test_empty_inserts(self):
        s = "no session"
        self.h.insert_gps_updates([], s)
        self.h.insert_imu_updates([], s)
        self.h.insert_can_updates([], s)
        self.h.insert_tpms_updates([], s)
