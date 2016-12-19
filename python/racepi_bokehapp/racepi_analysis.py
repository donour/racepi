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
from os import listdir

import pandas as pd
from bokeh.models.widgets import PreText, Select
from bokeh.models import ColumnDataSource, Range1d, LinearAxis
from bokeh.layouts import row, column
from bokeh.palettes import Blues4, Reds4
from sqlalchemy import create_engine
from bokeh.plotting import figure
from scipy.signal import savgol_filter
from bokeh.charts import Histogram, output_file, show

import can_data

# Focus RS Mk3 CAN converters
tps_converter = can_data.CanFrameValueExtractor(6, 10, a=0.1)
steering_angle_converter = can_data.CanFrameValueExtractor(49, 15, a=9.587e-5)
steering_direction_converter = can_data.CanFrameValueExtractor(32, 1)
rpm_converter = can_data.CanFrameValueExtractor(36, 12, a=2.0)
brake_pressure_converter = can_data.CanFrameValueExtractor(24, 16, a=1e-3)

class RacePiDBSession:

    def __init__(self, db_location):
        self.db = create_engine("sqlite:///" + db_location)
        # TODO: sanity check that expected tables exist

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

    def get_and_transform_can_data(self, session_id, arbitration_id, value_converter):
        data = pd.read_sql_query(
            "select timestamp, msg FROM %s where session_id='%s' and arbitration_id=%s" %
            ("can_data", session_id, arbitration_id), self.db, index_col='timestamp')
        data['result'] = \
            [value_converter.convert_frame(can_data.CanFrame('999', x)) for x in data.msg.tolist()]
        return data


class RunView:

    def __init__(self):
        self.session_selector = None
        self.stats = PreText(text='Run Stats', width=500, height=150)
        self.details = PreText(text='Run Details', width=300, height=100)
        self.speed_source = ColumnDataSource(data=dict(timestamp=[], speed=[], lat=[], lon=[]))
        self.accel_source = ColumnDataSource(data=dict(timestamp=[], x_accel=[]))
        self.tps_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.bps_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.rpm_source = ColumnDataSource(data=dict(timestamp=[], result=[]))


class RacePiAnalysis:

    @staticmethod
    def convert_dataframe_index_to_timedelta(dataframe):
        if not dataframe.empty:
            dataframe.index = dataframe.index - dataframe.index[0]

    def load_data(self, session_info, v):
        """

        :param session_info:
        :param v: view
        """
        session_id = session_info[0]
        gps_data = self.db.get_gps_data(session_id)
        imu_data = self.db.get_imu_data(session_id)

        can_channels = {
            'tps': self.db.get_and_transform_can_data(session_id, 128, tps_converter),
            'b_pres': self.db.get_and_transform_can_data(session_id, 531, brake_pressure_converter),
            'rpm': self.db.get_and_transform_can_data(session_id, 144, rpm_converter)
        }

        self.convert_dataframe_index_to_timedelta(gps_data)
        self.convert_dataframe_index_to_timedelta(imu_data)
        for c in can_channels:
            self.convert_dataframe_index_to_timedelta(imu_data)
            self.convert_dataframe_index_to_timedelta(can_channels[c])

        for k in imu_data:
            imu_data[k] = savgol_filter(imu_data[k], 13, 3)
        for k in gps_data:
            gps_data[k] = savgol_filter(gps_data[k], 13, 3)

        v.speed_source.data = ColumnDataSource(gps_data).data
        v.accel_source.data = ColumnDataSource(imu_data).data
        v.tps_source.data = ColumnDataSource(can_channels['tps']).data
        v.rpm_source.data = ColumnDataSource(can_channels['rpm']).data
        v.bps_source.data = ColumnDataSource(can_channels['b_pres']).data

        v.stats.text = str(gps_data.describe())
        v.details.text = "duration:%.0f\nVmax:%.0f\nsamples:%d" % session_info[2:5]

    def __init__(self, db_location):
        self.db = RacePiDBSession(db_location)
        self.sessions = {"%s:%.0f" % (datetime.fromtimestamp(s[1]).isoformat(), s[2]): s for s in self.db.get_sessions()}

        self.primary_view = pv = RunView()
        self.compare_view = cv = RunView()

        pv.session_selector = Select(options=self.sessions.keys())
        cv.session_selector = Select(options=self.sessions.keys())

        TOOLS=['pan, box_zoom, reset']
        s1 = figure(width=900, plot_height=200, title="Speed (m/s)", tools=TOOLS)
        s1.line('timestamp', 'speed', source=pv.speed_source, color=Blues4[0])
        s1.line('timestamp', 'speed', source=cv.speed_source, color=Reds4[0])
        s2 = figure(width=900, plot_height=200, title="Accel (g)", tools=TOOLS, x_range=s1.x_range, y_range=[-1.5, 1.5])
        s2.line('timestamp', 'x_accel', source=pv.accel_source, color=Blues4[0])
        s2.line('timestamp', 'x_accel', source=cv.accel_source, color=Reds4[0])
        s3 = figure(width=900, plot_height=200, title="Input", tools=TOOLS, x_range=s1.x_range)
        s3.line('timestamp', 'result', source=pv.bps_source, legend="PBrake", color=Blues4[0])
        s3.line('timestamp', 'result', source=cv.bps_source, legend="CBrake", color=Reds4[0])
        s3.extra_y_ranges = {"TPS": Range1d(start=0, end=100)}
        s3.add_layout(LinearAxis(y_range_name="TPS"), 'right')
        s3.line('timestamp', 'result', source=pv.tps_source, y_range_name="TPS", legend="PTPS", color=Blues4[1])
        s3.line('timestamp', 'result', source=cv.tps_source, y_range_name="TPS", legend="CTPS", color=Reds4[1])
        s4 = figure(width=900, plot_height=200, title="RPM", tools=TOOLS, x_range=s1.x_range)
        s4.line('timestamp', 'result', source=pv.rpm_source, color=Blues4[0])
        s4.line('timestamp', 'result', source=cv.rpm_source, color=Reds4[0])


        tps_hist = figure(width=900, plot_height=200, title="TPS", tools=TOOLS)
        hh1 = tps_hist.quad(bottom=0, left=[], right=[], top=[], alpha=0.5)
        # TODO finish tps histogram
        #self.tps_hist = Histogram({'result':[1]}, values='result', title="TPS", width=900, height=200, tools=TOOLS)
        #self.tps_hist = Histogram(pv.tps_source.data, values='result', title="TPS", width=900, height=200, tools=TOOLS)
        #tps_hist = Histogram(cv.tps_source, values='result', title="TPS")

        pv.session_selector.on_change('value', lambda a, o, n: self.load_data(self.sessions[n], self.primary_view))
        cv.session_selector.on_change('value', lambda a, o, n: self.load_data(self.sessions[n], self.compare_view))

        self.widgets = column(
            row(
                column(pv.session_selector, pv.details),
                column(cv.session_selector, cv.details)
            ),
            s1,
            s2,
            s3,
            s4,
            tps_hist,
            row(
                pv.stats,
                cv.stats
            )
        )




