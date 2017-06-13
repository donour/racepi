# Copyright 2016-7 Donour Sizemore
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

from uuid import uuid1
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from racepi_database_handler.objects import *
from racepi_sensor_handler.data_utilities import uptime_helper


class DbHandler:
    """
    Class for handling RacePi access to sqlite
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.db_session = None

    def connect(self):
        engine = create_engine('sqlite:///' + self.db_path)
        Base.metadata.bind = engine
        sm = sessionmaker(bind=engine)
        self.db_session = sm()
        self.db_session.execute("PRAGMA foreign_keys = ON;")
        self.db_session.execute("PRAGMA journal_mode = WAL;")

    def get_new_session(self):
        """
        Create new session entry in database
        The session name includes the current system uptime.

        :return: session id as UUID
        """
        if not self.db_session:
            raise RuntimeError("Database not connected")
        s = Session()
        s.id = str(uuid1())
        s.description = "Created by RacePi (uptime: %.0fs)" % uptime_helper()
        self.db_session.add(s)
        self.db_session.commit()
        return s.id

    def insert_gps_updates(self, gps_data, session_id):
        """
        :param gps_data:
        :param session_id:
        :return:
        """

        if not self.db_session:
            raise RuntimeWarning("No database connected")

        for sample in gps_data:
            t, data = sample
            v = GPSData()
            v.session_id = session_id
            v.timestamp = t

            # Set GPSd fields
            v.time = data.get("time")
            v.lat = data.get("lat")
            v.lon = data.get("lon")
            v.alt = data.get("alt")
            v.epv = data.get("epv")
            v.epx = data.get("epx")
            v.epy = data.get("epy")
            v.speed = data.get("speed")
            v.track = data.get("track")
            self.db_session.add(v)

        self.db_session.commit()

    def insert_imu_updates(self, imu_data, session_id):
        if not self.db_session:
            raise RuntimeWarning("No database connected")

        for sample in imu_data:
            if sample:
                t, data = sample
                pose = data.get('fusionPose')
                accel= data.get('accel')
                gyro = data.get('gyro')

                v = IMUData()
                v.session_id = session_id
                v.timestamp = t
                v.r, v.p, v.y = tuple(pose)
                v.x_accel, v.y_accel, v.z_accel = tuple(accel)
                v.x_gyro, v.y_gyro, v.z_gyro = tuple(gyro)

                self.db_session.add(v)

        self.db_session.commit()

    def insert_can_updates(self, can_data, session_id):
        if not self.db_session:
            raise RuntimeWarning("No database connected")

        for sample in can_data:
            t, raw = sample
            if len(raw) < 5:
                raise RuntimeWarning("Invalid can data: ", raw)
            else:
                arb_id = raw[:3]
                payload = raw[3:]
                v = CANData()
                v.timestamp = t
                v.session_id = session_id
                v.arbitration_id = int(arb_id, 16)
                v.rtr = 0
                v.msg = payload
                self.db_session.add(v)

        self.db_session.commit()

    def insert_tpms_updates(self, tpms_data, session_id):
        if not self.db_session:
            raise RuntimeWarning("No database connected")

        for sample in tpms_data:
            t, raw = sample
            lf_data = raw.get('lf')
            rf_data = raw.get('rf')
            lr_data = raw.get('lr')
            rr_data = raw.get('rr')
            lf_pressure = lf_data.get('pressure')
            rf_pressure = rf_data.get('pressure')
            lr_pressure = lr_data.get('pressure')
            rr_pressure = rr_data.get('pressure')

            lf_temp = lf_data.get('temp')
            rf_temp = rf_data.get('temp')
            lr_temp = lr_data.get('temp')
            rr_temp = rr_data.get('temp')

            lf_low_voltage = 1 if lf_data.get('low_voltage') else 0
            rf_low_voltage = 1 if rf_data.get('low_voltage') else 0
            lr_low_voltage = 1 if lr_data.get('low_voltage') else 0
            rr_low_voltage = 1 if rr_data.get('low_voltage') else 0

            v = TireData()
            v.session_id = session_id
            v.timestamp = t
            v.lf_pressure = lf_pressure
            v.rf_pressure = rf_pressure
            v.lr_pressure = lr_pressure
            v.rr_pressure = rr_pressure
            v.lf_temp = lf_temp
            v.rf_temp = rf_temp
            v.lr_temp = lr_temp
            v.rr_temp = rr_temp
            v.lf_sensor_battery = lf_low_voltage
            v.rf_sensor_battery = rf_low_voltage
            v.lr_sensor_battery = lr_low_voltage
            v.rr_sensor_battery = rr_low_voltage

            self.db_session.add(v)

        self.db_session.commit()

    def populate_session_info(self, session_id):
        """
        Populate the session info data with metadata from the
        sensor tables. The includes statistics about the session.

        :param session_id: The ID of the session
        :return:
        """

        #TODO replace this with an ORM implementation

        if not session_id:
            return
        if not self.db_session:
            raise RuntimeWarning("No database connected")
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
        self.db_session.execute(update_cmd)
        self.db_session.commit
