# Copyright 2018 Donour Sizemore
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
from racepi.database.objects import *
from racepi.database.processed_data_objects import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_db_session(filename):
    engine = create_engine('sqlite:///' + filename)
    Base.metadata.bind = engine
    sm = sessionmaker(bind=engine)
    s = sm()
    return s
