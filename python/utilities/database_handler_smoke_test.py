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

import sys
from racepi_database_handler import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s <sqlite db filename> ..." % sys.argv[0])
        sys.exit(1)
    dbfile = sys.argv[1]
    print("Opening %s" % dbfile)
    engine = create_engine('sqlite:///' + dbfile)
    Base.metadata.bind = engine
    sm = sessionmaker()
    sm.bind = engine
    s = sm()
    print("Connected to db, collecting stats:")
    print("Session count:     %08d" % len(s.query(Session).all()))
    print("SessionInfo count: %08d" % len(s.query(SessionInfo).all()))
    print("GPSData count:     %08d" % len(s.query(GPSData).all()))
    print("IMUData count:     %08d" % len(s.query(IMUData).all()))
    print("CANData count:     %08d" % len(s.query(CANData).all()))
