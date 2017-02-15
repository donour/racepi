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
from sqlalchemy import create_engine

import pandas as pd
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, Range1d, LinearAxis
from bokeh.models.widgets import PreText, Select
from bokeh.palettes import Blues4, Reds4
from bokeh.plotting import figure
from scipy.signal import savgol_filter

from racepi_can_decoder import can_data

# Focus RS Mk3 CAN converters
tps_converter = can_data.CanFrameValueExtractor(6, 10, a=0.1)
steering_angle_converter = can_data.CanFrameValueExtractor(49, 15, a=9.587e-5)
steering_direction_converter = can_data.CanFrameValueExtractor(32, 1)
rpm_converter = can_data.CanFrameValueExtractor(36, 12, a=2.0)
brake_pressure_converter = can_data.CanFrameValueExtractor(24, 16, a=1e-3)
wheelspeed1_converter = can_data.CanFrameValueExtractor(1, 15, a=1/307.0)
wheelspeed2_converter = can_data.CanFrameValueExtractor(17, 15, a=1/307.0)
wheelspeed3_converter = can_data.CanFrameValueExtractor(33, 15, a=1/307.0)
wheelspeed4_converter = can_data.CanFrameValueExtractor(49, 15, a=1/307.0)

RACEPI_MAP_SIZE = 600


class RacePiDBSession:

    def __init__(self, db_location):
        self.db = create_engine("sqlite:///" + db_location)
        # TODO: sanity check that expected tables exist

    def __get_sql_data(self, table, row_filter="1=1"):
        with self.db.connect() as c:
            q = c.execute("select * FROM %s where %s " % (table, row_filter))
            return q.cursor.fetchall()

    def get_sessions(self):
        return self.__get_sql_data("session_info", "max_speed>10")

    def get_gps_data(self, session_id):
        # no gps speed samples are really zero, but we only
        # need the ones that indicate motion
        return pd.read_sql_query(
            "select timestamp, speed, track, lat, lon FROM %s where speed>0.25 and session_id='%s'" %
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
        self.accel_source = ColumnDataSource(data=dict(timestamp=[], x_accel=[], y_accel=[]))
        self.tps_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.bps_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.rpm_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.wheelspeed1_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.wheelspeed2_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.wheelspeed3_source = ColumnDataSource(data=dict(timestamp=[], result=[]))
        self.wheelspeed4_source = ColumnDataSource(data=dict(timestamp=[], result=[]))

class RacePiAnalysis:

    @staticmethod
    def convert_dataframe_index_to_timedelta(dataframe, t0):
        if not dataframe.empty:
            dataframe.index = dataframe.index - t0

    def load_data(self, session_info, v):
        """

        :param session_info:
        :param v: view
        """
        session_id = session_info[0]
        gps_data = self.db.get_gps_data(session_id)
        imu_data = self.db.get_imu_data(session_id)

        try:
            can_channels = {
                 'tps': self.db.get_and_transform_can_data(session_id, 128, tps_converter),
                 'b_pres': self.db.get_and_transform_can_data(session_id, 531, brake_pressure_converter),
                 'rpm': self.db.get_and_transform_can_data(session_id, 144, rpm_converter),
                 'wheelspeed1': self.db.get_and_transform_can_data(session_id, 400, wheelspeed1_converter),
                 'wheelspeed2': self.db.get_and_transform_can_data(session_id, 400, wheelspeed2_converter),
                 'wheelspeed3': self.db.get_and_transform_can_data(session_id, 400, wheelspeed3_converter),
                 'wheelspeed4': self.db.get_and_transform_can_data(session_id, 400, wheelspeed4_converter)
            }
        except ValueError as e:
            print("Error loading can channels: " + str(e))
            can_channels = {}

        # find first time vehicle moved
        t0 = gps_data.index[0]
        self.convert_dataframe_index_to_timedelta(gps_data, t0)
        self.convert_dataframe_index_to_timedelta(imu_data, t0)
        for c in can_channels:
            self.convert_dataframe_index_to_timedelta(can_channels[c], t0)

        for k in imu_data:
            imu_data[k] = savgol_filter(imu_data[k], 31, 3)

        v.speed_source.data = ColumnDataSource(gps_data).data
        v.accel_source.data = ColumnDataSource(imu_data).data
        if 'tps' in can_channels:
            v.tps_source.data = ColumnDataSource(can_channels['tps']).data
        if 'rpm' in can_channels:
            v.rpm_source.data = ColumnDataSource(can_channels['rpm']).data
        if 'b_pres' in can_channels:
            v.bps_source.data = ColumnDataSource(can_channels['b_pres']).data
        if 'wheelspeed1' in can_channels:
            v.wheelspeed1_source.data = ColumnDataSource(can_channels['wheelspeed1']).data
        if 'wheelspeed2' in can_channels:
            v.wheelspeed2_source.data = ColumnDataSource(can_channels['wheelspeed2']).data
        if 'wheelspeed3' in can_channels:
            v.wheelspeed3_source.data = ColumnDataSource(can_channels['wheelspeed3']).data
        if 'wheelspeed4' in can_channels:
            v.wheelspeed4_source.data = ColumnDataSource(can_channels['wheelspeed4']).data

        v.stats.text = str(gps_data.describe())
        v.details.text = "duration:%.0f\nVmax:%.0f\nsamples:%d" % session_info[2:5]

    def __init__(self, db_location):
        self.db = RacePiDBSession(db_location)
        self.sessions = {"%s:%.0f" % (datetime.fromtimestamp(s[1]).isoformat(), s[2]): s for s in self.db.get_sessions()}

        self.primary_view = pv = RunView()
        self.compare_view = cv = RunView()

        pv.session_selector = Select(options=sorted(self.sessions.keys()), width=200)
        cv.session_selector = Select(options=sorted(self.sessions.keys()), width=200)

        TOOLS=['pan, box_zoom, reset']
        s1 = figure(width=900, plot_height=200, title="Speed (m/s)", tools=TOOLS)
        s1.line('timestamp', 'speed', source=pv.speed_source, color=Blues4[0])
        s1.line('timestamp', 'speed', source=cv.speed_source, color=Reds4[0])
        x_accel_fig = figure(width=900, plot_height=200, title="X Accel (g)", tools=TOOLS, x_range=s1.x_range, y_range=[-2, 2])
        x_accel_fig.line('timestamp', 'x_accel', source=pv.accel_source, color=Blues4[0])
        x_accel_fig.line('timestamp', 'x_accel', source=cv.accel_source, color=Reds4[0])
        y_accel_fig = figure(width=900, plot_height=200, title="Y Accel (g)", tools=TOOLS, x_range=s1.x_range, y_range=[-1.25, 1.25])
        y_accel_fig.line('timestamp', 'y_accel', source=pv.accel_source, color=Blues4[0])
        y_accel_fig.line('timestamp', 'y_accel', source=cv.accel_source, color=Reds4[0])
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

        wheelspeed_fig = figure(width=900, plot_height=200, title="Wheelspeeds", tools=TOOLS, x_range=s1.x_range)
        wheelspeed_fig.line('timestamp', 'result', source=pv.wheelspeed1_source, legend="P1", color=Blues4[0])
        wheelspeed_fig.line('timestamp', 'result', source=cv.wheelspeed1_source, legend="C1", color=Reds4[0])
        wheelspeed_fig.line('timestamp', 'result', source=pv.wheelspeed2_source, legend="P2", color=Blues4[1])
        wheelspeed_fig.line('timestamp', 'result', source=cv.wheelspeed2_source, legend="C2", color=Reds4[1])
        wheelspeed_fig.line('timestamp', 'result', source=pv.wheelspeed3_source, legend="P3", color=Blues4[1])
        wheelspeed_fig.line('timestamp', 'result', source=cv.wheelspeed3_source, legend="C3", color=Reds4[1])
        wheelspeed_fig.line('timestamp', 'result', source=pv.wheelspeed4_source, legend="P4", color=Blues4[1])
        wheelspeed_fig.line('timestamp', 'result', source=cv.wheelspeed4_source, legend="C4", color=Reds4[1])

        # TODO scale distances to appear as more reasonable projections
        # 1.2 is a hack to work around 35 deg latitude
        map_fig = figure(width=RACEPI_MAP_SIZE, height=int(RACEPI_MAP_SIZE*1.2), title="Map", tools=TOOLS)
        map_fig.line('lon', 'lat', source=pv.speed_source, color=Blues4[0])
        map_fig.line('lon', 'lat', source=cv.speed_source, color=Reds4[0])

        minimap_fig = figure(width=150, height=150, tools=[])
        minimap_fig.line('lon', 'lat', source=pv.speed_source, color=Blues4[0])
        minimap_fig.line('lon', 'lat', source=cv.speed_source, color=Reds4[0])
        minimap_fig.axis.visible=False

        g_g_fig = figure(width=200, height=150, tools=[])
        g_g_fig.circle('x_accel', 'y_accel', source=pv.accel_source, color=Blues4[0], size=2)
        g_g_fig.circle('x_accel', 'y_accel', source=cv.accel_source, color=Reds4[0], size=2)


        #tps_hist = figure(width=900, plot_height=200, title="TPS", tools=TOOLS)
        #hh1 = tps_hist.quad(bottom=0, left=[], right=[], top=[], alpha=0.5)
        # TODO finish tps histogram
        #self.tps_hist = Histogram({'result':[1]}, values='result', title="TPS", width=900, height=200, tools=TOOLS)
        #self.tps_hist = Histogram(pv.tps_source.data, values='result', title="TPS", width=900, height=200, tools=TOOLS)
        #tps_hist = Histogram(cv.tps_source, values='result', title="TPS")

        pv.session_selector.on_change('value', lambda a, o, n: self.load_data(self.sessions[n], self.primary_view))
        cv.session_selector.on_change('value', lambda a, o, n: self.load_data(self.sessions[n], self.compare_view))

        self.widgets = column(
            row(
                column(pv.session_selector, pv.details),
                column(cv.session_selector, cv.details),
                g_g_fig,
                minimap_fig
            ),
            s1,
            x_accel_fig,
            y_accel_fig,
            s3,
            s4,
            wheelspeed_fig,
            map_fig,
            row(
                pv.stats,
                cv.stats
            )

        )




