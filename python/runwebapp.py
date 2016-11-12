#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
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

from sqlalchemy import create_engine
from racepi_webapp import app

DEFAULT_SQLITE_FILE = '/external/racepi_data/test.db'

if __name__ == "__main__":   
    import sys, logo  # display logo

    if len(sys.argv) < 2:
        dbfile = DEFAULT_SQLITE_FILE
    else:
        dbfile = sys.argv[1]

    app.db = create_engine("sqlite:///"+dbfile)
    # FIXME: disabling debugging causes 100% cpu usage, notifier?
    app.run(host='0.0.0.0', threaded=True)

