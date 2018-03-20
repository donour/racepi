#!/usr/bin/env python3
#  Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
"""
This is a tool to replay recorded sessions via the DL1 broadcast
library.
"""

import sys

import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from racepi.racetech.writers import RaceTechnologyDL1FeedWriter
from racepi_database_handler import Base, SessionInfo, GPSData, IMUData, CANData
from racepi.sensor.data_utilities import merge_and_generate_ordered_log


BLUETOOTH_CLIENT_WAIT_SECONDS = 0.1


def replay(db_file, session_id):
    print("Opening %s" % db_file)
    engine = create_engine('sqlite:///' + db_file)
    Base.metadata.bind = engine
    sm = sessionmaker()
    sm.bind = engine
    s = sm()

    writer = RaceTechnologyDL1FeedWriter()

    print("Waiting for active clients")
    while writer.number_of_clients() <= 0:
        time.sleep(BLUETOOTH_CLIENT_WAIT_SECONDS)

    for si in s.query(SessionInfo).filter(SessionInfo.max_speed > 10).all():
        if session_id and si.session_id != session_id:
            continue  # skip if different session_id specified

        data = {}
        # load all data for session
        gps_data = s.query(GPSData).filter(GPSData.session_id == si.session_id).all()
        imu_data = s.query(IMUData).filter(IMUData.session_id == si.session_id).all()
        can_data = s.query(CANData).filter(CANData.session_id == si.session_id).all()

        # construct replay messages
        data['gps'] = [(x.timestamp, {'speed': x.speed, 'lat': x.lat, 'lon': x.lon, 'alt': x.alt})
                       for x in gps_data]
        data['imu'] = [(x.timestamp, {'accel': (x.x_accel, x.y_accel, x.z_accel)})
                       for x in imu_data]
        data['can'] = [(x.timestamp, "%03x%s" % (x.arbitration_id, x.msg))
                       for x in can_data]

        flat_data = merge_and_generate_ordered_log(data)

        for val in flat_data:
            if val:
                if val[0] == 'gps':
                    writer.write_gps_sample(val[1], val[2])
                elif val[0] == 'imu':
                    writer.write_imu_sample(val[1], val[2])
                elif val[0] == 'can':
                    writer.write_can_sample(val[1], val[2])
                    writer.flush_queued_messages()  # can messages are delivered very quickly, flush often

        writer.flush_queued_messages()
        print("Finished", si.session_id)
        # sleep between replays
        time.sleep(4)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s <sqlite db filename> [session_id]" % sys.argv[0])
        sys.exit(1)
    db_file = sys.argv[1]
    if len(sys.argv) > 2:
        session_id = sys.argv[2]
    else:
        session_id = None
    replay(db_file, session_id)
