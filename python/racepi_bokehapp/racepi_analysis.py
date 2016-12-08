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

from datetime import datetime

import pandas as pd
from bokeh.models.widgets import PreText, Select
from bokeh.models import ColumnDataSource
from bokeh.layouts import row, column
from sqlalchemy import create_engine
from bokeh.plotting import figure

DEFAULT_SQLITE_FILE = '/home/donour/crimson_day.db'


class RacePiDBSession:

    def __init__(self, db_location=DEFAULT_SQLITE_FILE):
        self.db = create_engine("sqlite:///" + db_location)

    def __get_sql_data(self, table, row_filter="1=1"):
        with self.db.connect() as c:
            q = c.execute("select * FROM %s where %s " % (table, row_filter))
            return q.cursor.fetchall()

    def get_sessions(self):
        return self.__get_sql_data("session_info")

    def get_gps_data(self, session_id):
        return pd.read_sql_query(
            "select timestamp, speed, track, lat, lon FROM %s where session_id='%s'" %
            ("gps_data", session_id), self.db, index_col='timestamp')

    def get_imu_data(self, session_id):
        return pd.read_sql_query(
            "select timestamp, x_accel, y_accel, z_accel FROM %s where session_id='%s'" %
            ("imu_data", session_id), self.db, index_col='timestamp')


class RunView:

    def __init__(self):
        self.session_selector = None
        self.stats = PreText(text='', width=500, height=150)
        self.details = PreText(text='', width=300, height=100)
        self.speed_source = ColumnDataSource(data=dict(timestamp=[], speed=[], lat=[], lon=[]))
        self.accel_source = ColumnDataSource(data=dict(timestamp=[], x_accel=[]))


class RacePiAnalysis:

    def load_data(self, session_info, v):


        # TODO convert all timestamps to deltas

        # load primary run data
        session_id = session_info[0]
        gps_data = self.db.get_gps_data(session_id)
        imu_data = self.db.get_imu_data(session_id)
        gps_data = gps_data.rolling(min_periods=1, window=8, center=True).mean()
        imu_data = imu_data.rolling(min_periods=1, window=32, center=True).mean()

        v.speed_source.data = ColumnDataSource(gps_data).data
        v.accel_source.data = ColumnDataSource(imu_data).data
        v.stats.text = str(gps_data.describe())
        v.details.text = "date:%s\nduration:%.0f\nVmax:%.0f\nsamples:%d" % session_info[1:5]

    def session_change_primary(self, attrname, old, new):
        self.load_data(self.sessions[new], self.primary_view)

    def session_change_compare(self, attrname, old, new):
        self.load_data(self.sessions[new], self.compare_view)

    def __init__(self):
        self.db = RacePiDBSession()
        self.sessions = {"%s:%.0f" % (datetime.fromtimestamp(s[1]).isoformat(), s[2]): s for s in self.db.get_sessions()}

        self.primary_view = pv = RunView()
        self.compare_view = cv = RunView()

        pv.session_selector = Select(options=self.sessions.keys())
        cv.session_selector = Select(options=self.sessions.keys())

        s1 = figure(width=800, plot_height=200, title="speed")
        s1.line('timestamp', 'speed', source=pv.speed_source)
        s1.line('timestamp', 'speed', source=cv.speed_source)
        s2 = figure(width=800, plot_height=200, title="xaccel", x_range=s1.x_range, y_range=[-1.5, 1.5], tools=[])
        s2.line('timestamp', 'x_accel', source=pv.accel_source)
        s2.line('timestamp', 'x_accel', source=cv.accel_source)

        pv.session_selector.on_change('value', self.session_change_primary)
        cv.session_selector.on_change('value', self.session_change_compare)

        self.widgets = column(
            row(
                column(pv.session_selector, pv.details),
                column(cv.session_selector, cv.details)
            ),
            s1,
            s2,
            pv.stats
        )




