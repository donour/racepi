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

import pandas as pd
from bokeh.models.widgets import PreText, Select
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import row, column
from sqlalchemy import create_engine
from bokeh.plotting import figure


def get_sql_data(db, table, row_filter="1=1"):
    with db.connect() as c:
        q = c.execute("select * FROM %s where %s " % (table, row_filter))
        return q.cursor.fetchall()

DEFAULT_SQLITE_FILE = '/home/donour/crimson_day.db'
db = create_engine("sqlite:///"+DEFAULT_SQLITE_FILE)
sessions = {s[0]: s for s in get_sql_data(db, "session_info")}

session_selector = Select(options=sessions.keys())

# set up layout
stats = PreText(text='', width=500, height=150)

speed_source = ColumnDataSource(data=dict(timestamp=[], speed=[], lat=[], lon=[]))
accel_source = ColumnDataSource(data=dict(timestamp=[], x_accel=[]))
s1 = figure(width=800, plot_height=200, title="speed")
s1.line('timestamp', 'speed', source=speed_source)
s2 = figure(width=800, plot_height=200, title="xaccel", x_range=s1.x_range)
s2.line('timestamp', 'x_accel', source=accel_source)


def session_change(attrname, old, new):
    load_data(new)


def load_data(session_id=session_selector.value):
    gps_data = pd.read_sql_query("select timestamp, speed, track, lat, lon FROM %s where session_id='%s'" % ("gps_data", session_id), db, index_col='timestamp')
    imu_data = pd.read_sql_query("select timestamp, x_accel, y_accel, z_accel FROM %s where session_id='%s'" % ("imu_data", session_id), db, index_col='timestamp')
    gps_data = gps_data.rolling(min_periods=1, window=8, center=True).mean()
    imu_data = imu_data.rolling(min_periods=1, window=32, center=True).mean()

    speed_source.data = ColumnDataSource(gps_data).data
    accel_source.data = ColumnDataSource(imu_data).data
    stats.text = str(gps_data.describe())

session_selector.on_change('value', session_change)
widgets = column(row(stats,session_selector), s1, s2)
curdoc().add_root(widgets)
curdoc().title = "RacePI :: Analysis"

