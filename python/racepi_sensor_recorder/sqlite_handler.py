# Copyright 2016 Donour Sizemore
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

import sqlite3
import uuid

from racepi_sensor_handler.data_utilities import uptime_helper

#TODO rewrite to use DB bindings

class DbHandler:
    """
    Class for handling RacePi access to sqlite
    """
    def __init__(self, db_location, gps_fields=[]):
        self.db_location = db_location
        self.gps_fields = gps_fields
        
    def connect(self):

        self.conn = sqlite3.connect(self.db_location)
        if self.conn is None:
            raise IOError("Could not open db: " + self.db_location)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")
        
    def get_new_session(self):
        """
        Create new session entry in database
        The session name includes the current system uptime.

        :return: session id as UUID
        """
        session_id = uuid.uuid1()
        insert_cmd = """
        insert into sessions (id, description)
        values ('%s', 'Created by RacePi (uptime: %.0fs)')
        """ % (session_id.hex, uptime_helper())
        self.conn.execute(insert_cmd)
        self.conn.commit()
        return session_id

    def insert_imu_updates(self, imu_data, session_id):
        for sample in imu_data:
            if sample:
                t = sample[0]
                pose = sample[1]['fusionPose']
                accel= sample[1]['accel']
                gyro = sample[1]['gyro']

                insert_cmd = """
                  insert into imu_data
                  (session_id, timestamp,
                   r, p, y, x_accel, y_accel, z_accel, x_gyro, y_gyro, z_gyro)
                  values
                  ('%s', %s,
                   %f, %f, %f, %f, %f, %f, %f, %f, %f)
                """ % (
                    (session_id.hex, t) +
                     tuple(pose) + tuple(accel) + tuple(gyro))
                self.conn.execute(insert_cmd)

        if imu_data:
            self.conn.commit()

    def insert_gps_updates(self, gps_data, session_id):
        
        for sample in gps_data:
            # system time of sample
            t = sample[0]   
            # extract just the fields we use
            d = map(sample[1].get, self.gps_fields)
            available_fields = sample[1].keys()          
            # the sample is only usable if it has velocity
            if 'speed' in available_fields:                
                insert_cmd = """
                  insert into gps_data
                  (session_id, timestamp,
                   %s)
                  values
                  ('%s', %s,
                   '%s', %f, %f, %f, %f, %f, %f, %f, %f)
                """ % (
                    (','.join(self.gps_fields),
                    session_id.hex, t) + tuple(d))
                self.conn.execute(insert_cmd)

        if gps_data:
            self.conn.commit()

    def insert_can_updates(self, can_data, session_id):
        for sample in can_data:
            t, raw = sample
            if len(raw) < 5:
                raise TypeError("Invalid can data:" + raw)

            arbId = raw[:3]
            payload = raw[3:]
            insert_cmd = """
              insert into can_data
              (session_id, timestamp, arbitration_id, rtr, msg)
              values
              ('%s', %s, %d, %d, '%s')
            """ % (
                (session_id.hex, t, int(arbId, 16), 0, payload))            
            self.conn.execute(insert_cmd)

        if can_data:
            self.conn.commit()

    def populate_session_info(self, session_id):
        """
        Populate the session info data with metadata from the
        sensor tables
        """

        if not session_id:
            return
        
        update_cmd = """
INSERT OR REPLACE into session_info
(session_id, start_time_utc, max_speed, num_data_samples, duration)
    select
        sessions.id as session_id,
        start_time_utc,
        max_speed,
        gps_count+imu_count+ COALESCE(can_count,0) as num_data_samples,
        stop_time-start_time_utc as duration
from sessions
join
    (select session_id,count(distinct timestamp) as gps_count, MAX(speed) as max_speed, MIN(timestamp) as start_time_utc, MAX(timestamp) as stop_time
    from gps_data group by session_id) as gps
    on gps.session_id = sessions.id
left join
    (select session_id,count(distinct timestamp) as imu_count
    from imu_data group by session_id) as imu
    on imu.session_id = sessions.id
left join
    (select session_id,count(distinct timestamp) as can_count
    from can_data group by session_id) as can
    on can.session_id = sessions.id
        where sessions.id = '%s'
        """ % session_id.hex

        self.conn.execute(update_cmd)
        self.conn.commit()

