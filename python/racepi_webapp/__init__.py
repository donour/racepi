# Copyright 2016-7 Donour Sizemore
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

from functools import lru_cache

from .plotly_helpers import get_scatterplot
from flask import Flask, jsonify, request, Response, abort
from plotly import graph_objs as pgo
from plotly import tools
import pandas as pd
from racepi_can_decoder import *
from racepi_database_handler import *
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
try:
    from flask_compress import Compress
    Compress(app)
    print("Text response compression enabled")
except ImportError:
    print("Compress library not found")

# TODO: sanitize all sql statements by remove ; character


def get_orm_session():
    Base.metadata.bind = app.db
    sm = sessionmaker()
    sm.bind = app.db
    return sm()


def get_and_transform_can_data(session_id, arbitration_id, value_converter):
    s = get_orm_session()

    data = [{'timestamp': x.timestamp,
            'value': value_converter.convert_frame(CanFrame("999", x.msg))}
            for x in
            s.query(CANData).filter(CANData.session_id == session_id).filter(CANData.arbitration_id == arbitration_id)
            ]
    return data


@app.route('/data/sessions')
def get_sessions():
    return get_sql_data("session_info", "1=1")


@app.route('/data/gps/<session_id>')
@lru_cache(maxsize=32)
def get_gps_data(session_id):
    s = get_orm_session()
    results = [{
                'timestamp': x.timestamp,
                'speed': x.speed,
                'lat': x.lat,
                'lon': x.lon,
                }
                for x in
                s.query(GPSData).filter(GPSData.session_id == session_id).all()]
    return jsonify(data=results, session_id=session_id)


@app.route('/data/imu/<session_id>')
@lru_cache(maxsize=32)
def get_imu_data(session_id):
    s = get_orm_session()
    results = [{
                'timestamp': x.timestamp,
                'x_accel': x.x_accel,
                'y_accel': x.y_accel,
                'z_accel': x.z_accel
                }
                for x in
                s.query(IMUData).filter(IMUData.session_id == session_id).all()]
    return jsonify(data=results, session_id=session_id)


@app.route('/data/can/<channel>/<session_id>')
@lru_cache(maxsize=32)
def get_can_data(channel, session_id):

    data = None
    if channel == "tps":
        data = get_and_transform_can_data(session_id, 128, focus_rs_tps_converter)
    elif channel == "rpm":
        data = get_and_transform_can_data(session_id, 144, focus_rs_rpm_converter)
    elif channel == "brake":
        data = get_and_transform_can_data(session_id, 531, focus_rs_brake_pressure_converter)
    elif channel == "steering":
        data = get_and_transform_can_data(session_id, 16, focus_rs_steering_angle_converter)
    if data is not None:
        return jsonify(data=data, channel=channel, session_id=session_id)
    else:
        abort(404)


###################################

def get_sql_data(table, query_filter):
    with app.db.connect() as c:
        q = c.execute("select * FROM %s where %s " % (table, query_filter))
        return jsonify(result=q.cursor.fetchall(), columns=q.keys())


def get_data(table):
    session_id = request.args.get("session_id")
    return get_sql_data(table, "session_id = '%s' ORDER BY timestamp" % session_id)


@app.route('/')
def hello_world():
    return app.send_static_file('index.html')


@app.route('/data/stats/<session_id>')
def get_stats_session(session_id):
    return jsonify(data="")


@app.route('/plot/accel')
@lru_cache(maxsize=32)
def get_plot_timeseries():
    session_id = request.args.get("session_id")
    # TODO fail on bad session_id
    with app.db.connect() as c:
        q = c.execute("select timestamp,x_accel,y_accel,z_accel FROM %s where %s " % ("imu_data", "session_id='%s'" % session_id))
        t = []
        x = []
        y = []
        z = []
        data = q.cursor.fetchall()
        t0 = data[0][0]
        map(lambda p: t.append(round(p[0]-t0, 3)), data)
        map(lambda p: x.append(round(p[1], 3)), data)
        map(lambda p: y.append(round(p[2], 3)), data)
        map(lambda p: z.append(round(p[3], 3)), data)
        data = [
            pgo.Scatter(x=t, y=x, name="x"),
            pgo.Scatter(x=t, y=y, name="y"),
            pgo.Scatter(x=t, y=z, name="z")

        ]
        layout = pgo.Layout(
            title="Accel",
            xaxis=dict(title="time"),
            yaxis=dict(title="val"),
        )
        fig = pgo.Figure(data=data, layout=layout)
        return jsonify(data=fig.get('data'), layout=fig.get('layout'))


@app.route('/plot/gps')
@lru_cache(maxsize=32)
def get_gpsplot_timeseries():
    session_id = request.args.get("session_id")
    # TODO fail on bad session_id
    with app.db.connect() as c:
        q = c.execute("select timestamp,speed,track FROM %s where %s " % ("gps_data", "session_id='%s'" % session_id))
        t = []
        x = []
        y = []
        data = q.cursor.fetchall()
        t0 = data[0][0]
        map(lambda p: t.append(p[0]-t0), data)
        map(lambda p: x.append(p[1]*2.23), data)
        map(lambda p: y.append(p[2]), data)
        data = [
            pgo.Scatter(x=t, y=x, name="speed"),
            pgo.Scatter(x=t, y=y, name="track", yaxis='y2'),

        ]
        layout = pgo.Layout(
            title="GPS",
            xaxis=dict(title="time"),
            yaxis=dict(title="val"),
            yaxis2=dict(
                title='yaxis2 title',
                titlefont=dict(
                    color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                    color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
            )
        )
        fig = pgo.Figure(data=data, layout=layout)
        return jsonify(data=fig.get('data'), layout=fig.get('layout'))


@app.route('/plot/run')
@lru_cache(maxsize=32)
def get_singlerun_timeseries():
    session_id = request.args.get("session_id")
    if 'smooth' in request.args:
        smoothing_window = int(request.args.get("smooth"))
    else:
        smoothing_window = 10

    can_channels = {
        'TPS (%)': get_and_transform_can_data(session_id, 128, focus_rs_tps_converter),
        'Brake Pressure (kPa)': get_and_transform_can_data(session_id, 531, focus_rs_brake_pressure_converter),
        'RPM': get_and_transform_can_data(session_id, 144, focus_rs_rpm_converter)
    }
    gps_data = pd.read_sql_query("select timestamp, speed, track, lat, lon FROM %s where session_id='%s'" % ("gps_data", session_id), app.db, index_col='timestamp')
    imu_data = pd.read_sql_query("select timestamp, x_accel, y_accel, z_accel FROM %s where session_id='%s'" % ("imu_data", session_id), app.db, index_col='timestamp')
    can_samples = pd.read_sql_query("select timestamp, msg FROM %s where session_id='%s' and arbitration_id=16" % ("can_data", session_id), app.db, index_col='timestamp')

    can_samples['Steering'] = [
        (focus_rs_steering_angle_converter.convert_frame(CanFrame('010', x)) * 3000 *
         ((-1)* focus_rs_steering_angle_converter.convert_frame(CanFrame('010', x))))
        for x in can_samples.msg.tolist()]

    fig = tools.make_subplots(rows=6, cols=1)
    fig.append_trace(get_scatterplot(gps_data.speed, smoothing_window, "Speed (m/s)"), 1, 1)
    fig.append_trace(get_scatterplot(imu_data.y_accel, smoothing_window << 3, "YAccel (avg)"), 2, 1)
    fig.append_trace(get_scatterplot(imu_data.x_accel, smoothing_window << 3, "XAccel (avg)"), 2, 1)
    fig.append_trace(get_scatterplot(can_samples['Steering'], smoothing_window, "Steering"), 3, 1)
    i = 4
    for c in can_channels:
        fig.append_trace(get_scatterplot(can_channels[c].result, smoothing_window, c), int(i), 1)
        i += 0.5

    return jsonify(data=fig.get('data'), layout=fig.get('layout'))


@app.route('/plot/speed')
@lru_cache(maxsize=32)
def get_plots_speed():
    session_id = request.args.get("session_id")
    smoothing_window = 10

    can_channels = {
        'TPS (%)': get_and_transform_can_data(session_id, 128, focus_rs_rpm_converter),
        'Brake Pressure (kPa)': get_and_transform_can_data(session_id, 531, focus_rs_brake_pressure_converter),
    }
    gps_data = pd.read_sql_query("select timestamp, speed, track, lat, lon FROM %s where session_id='%s'" % ("gps_data", session_id), app.db, index_col='timestamp')

    sources = [(gps_data.speed, smoothing_window, "Speed (m/s)")]
    for c in can_channels:
        sources.append((can_channels[c].result, smoothing_window, c))

    fig = plotly_helpers.get_xy_combined_plot(sources, "Speed")
    return jsonify(data=fig.get('data'), layout=fig.get('layout'))


@app.route('/export/csv')
def get_run_csv():
    session_id = request.args.get("session_id")
    get_csv_cmd="""
select * from
(select
    session_id,timestamp,'GPS' as type,time,speed,track,lat,lon,epx,epy,epv
    NULL as arbitration_id,NULL as msg,
    NULL AS r,NULL AS p,NULL AS y,NULL AS x_accel,NULL AS y_accel,NULL AS z_accel,NULL AS x_gyro,NULL AS y_gyro,NULL AS z_gyro
    from gps_data
union
select
    session_id,timestamp,'CAN' as type, NULL as time, NULL as speed,NULL as track,NULL as lat,NULL as lon,NULL as epx,NULL as epy,NULL as epv,
    arbitration_id, msg,
    NULL AS r,NULL AS p,NULL AS y,NULL AS x_accel,NULL AS y_accel,NULL AS z_accel,NULL AS x_gyro,NULL AS y_gyro,NULL AS z_gyro
    from can_data
union
select
    session_id,timestamp,'IMU' as type, NULL as time, NULL as speed,NULL as track,NULL as lat,NULL as lon,NULL as epx,NULL as epy,NULL as epv,
    NULL as arbitration_id, NULL as msg,
    r,p,y,x_accel,y_accel,z_accel,x_gyro,y_gyro,z_gyro
    from imu_data )


where session_id = '%s'
    """ % session_id
    with app.db.connect() as c:
        q = c.execute(get_csv_cmd)
        results = ["#" + ','.join(q.keys())]
        for row in q:
            data = [str(x) if x else '' for x in row]
            results.append(','.join(data))

        # only column header available
        if len(results) <= 1:
            raise ValueError("Invalid session")

        result = '\n'.join(results)
        return Response(result, mimetype='text/csv')


@app.route('/plot/bokeh_test/<session_id>')
def get_plots_bokeh_test(session_id):

    from bokeh.embed import components
    from bokeh.plotting import figure
    from bokeh.layouts import gridplot
    from bokeh.resources import INLINE
    from bokeh.util.string import encode_utf8
    import flask

    can_channels = {
        'TPS (%)': get_and_transform_can_data(session_id, 128, tps_converter),
        'Brake Pressure (kPa)': get_and_transform_can_data(session_id, 531, brake_pressure_converter),
    }
    gps_data = pd.read_sql_query("select timestamp, speed, track, lat, lon FROM %s where session_id='%s'" % ("gps_data", session_id), app.db, index_col='timestamp')
    imu_data = pd.read_sql_query("select timestamp, x_accel, y_accel, z_accel FROM %s where session_id='%s'" % ("imu_data", session_id), app.db, index_col='timestamp')

    gps_data = gps_data.rolling(min_periods=1, window=8, center=True).mean()
    imu_data = imu_data.rolling(min_periods=1, window=32, center=True).mean()

    s1 = figure(width=800, plot_height=250, title="speed")
    s1.line(gps_data.index, gps_data.speed)
    s2 = figure(width=800, plot_height=250, title="xaccel", x_range=s1.x_range)
    s2.line(imu_data.index, imu_data.x_accel)
    subplots = [[s1],[s2]]
    for c in can_channels:
        s = figure(width=800, plot_height=250, title=c, x_range=s1.x_range)
        s.line(can_channels[c].index, can_channels[c].result)
        subplots.append([s])
        print("added")

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script, div = components(gridplot(subplots))
    html = flask.render_template(
        'embed.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
    )
    return encode_utf8(html)
