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

# TODO finish ORM code

from sqlalchemy import Column, ForeignKey, Integer, String, Binary, BLOB, TEXT, DATETIME, REAL, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"
    id = Column(TEXT, primary_key=True, unique=True, nullable=False)
    description = Column(String())


class SessionInfo(Base):
    __tablename__ = 'session_info'
    session_id = Column(TEXT, ForeignKey("sessions.id"), unique=True, primary_key=True, nullable=False)
    start_time_utc = Column(REAL, nullable=False)
    duration = Column(REAL)
    max_speed = Column(REAL)
    num_data_samples = Column(Integer)


class IMUData(Base):
    __tablename__ = "imu_data"
    session_id = Column(TEXT, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(REAL, nullable=False, primary_key=True)
    r = Column(REAL)
    p = Column(REAL)
    y = Column(REAL)
    x_accel = Column(REAL)
    y_accel = Column(REAL)
    z_accel = Column(REAL)
    x_gyro = Column(REAL)
    y_gyro = Column(REAL)
    z_gyro = Column(REAL)


class GPSData(Base):
    __tablename__ = "gps_data"
    session_id = Column(TEXT, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(REAL, primary_key=True, nullable=False)
    time = Column(VARCHAR)
    lat = Column(REAL)
    lon = Column(REAL)
    speed = Column(REAL)
    track = Column(REAL)
    epx = Column(REAL)
    epy = Column(REAL)
    epv = Column(REAL)
    alt = Column(REAL)


class CANData(Base):
    __tablename__ = "can_data"
    session_id = Column(TEXT, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(REAL, primary_key=True, nullable=False)
    arbitration_id = Column(Integer, nullable=False)  # base (11bit) or extended (29bit)
    rtr = Column(Integer, nullable=False)  # 0 for data frames, 1 for data requests
    msg = Column(TEXT, nullable=False)  # data payload, string of 8 hexidecimal bytes


class TireData(Base):
    __tablename__ = "tire_data"
    session_id = Column(TEXT, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(REAL, primary_key=True, nullable=False)
    lf_pressure = Column(REAL)
    rf_pressure = Column(REAL)
    lr_pressure = Column(REAL)
    rr_pressure = Column(REAL)
    lf_temp = Column(REAL)
    rf_temp = Column(REAL)
    lr_temp = Column(REAL)
    rr_temp = Column(REAL)
