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

import sys

import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from racepi_racetechnology_writer.writers import RaceTechnologyDL1FeedWriter
from racepi_database_handler import Base, SessionInfo, GPSData, IMUData, CANData
from racepi_sensor_handler.data_utilities import merge_and_generate_ordered_log


def replay(dbfile):
    print("Opening %s" % dbfile)
    engine = create_engine('sqlite:///' + dbfile)
    Base.metadata.bind = engine
    sm = sessionmaker()
    sm.bind = engine
    s = sm()

    writer = RaceTechnologyDL1FeedWriter()

    print("Waiting for active clients")
    #while writer.number_of_clients() <= 0:
    #    time.sleep(0.1)

    for si in s.query(SessionInfo).all():
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
        writer.flush_queued_messages()

        # sleep between replays
        print("Finished", si.session_id)
        time.sleep(4)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s <sqlite db filename> ..." % sys.argv[0])
        sys.exit(1)
    dbfile = sys.argv[1]
    replay(dbfile)
