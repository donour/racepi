# Copyright 2016 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

# Main entry point for bokeh app

import os
from bokeh.io import curdoc
from racepi_bokehapp.racepi_analysis import RacePiAnalysis

DEFAULT_SQLITE_FILE = '/external/racepi_data/test.db'
#DEFAULT_SQLITE_FILE = '/home/donour/houston.db'

if not os.path.exists(DEFAULT_SQLITE_FILE):
    raise IOError("Missing DB file: " + DEFAULT_SQLITE_FILE)

curdoc().add_root(RacePiAnalysis(DEFAULT_SQLITE_FILE).widgets)
curdoc().title = "RacePI :: Analysis"

