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

from flask import Flask, jsonify, request, Response
from sqlalchemy import create_engine
from plotly import graph_objs as pgo
import pandas as pd

app = Flask(__name__)
db = create_engine('sqlite:////external/racepi_data/test.db')


def sfl(float_list, ndigits = 3):
    """
    Shorten a list of float by rounding to a small number of
    decimals. This significantly speeds up loading large datasets
    as JSON
    :param float_list: list of float values
    :param ndigits: number of rounding digits
    :return: list of values round to small number of digits
    """
    return [round(x, ndigits) for x in float_list]


def get_scatterplot(series, w, title):
    """
    Generate plotly scatter plot from pandas timeseries data

    :param series: plot dataframe series
    :param w: rolling averge window radius
    :param title: title for plot
    :return: scatterplot graph object
    """
    data = pd.Series(series).rolling(window=w, center=True).mean()
    t0 = data.index.values.tolist()[0]
    data.offset_time = [x-t0 for x in data.index.values.tolist()]
    return pgo.Scatter(x=sfl(data.offset_time[w:-w]), y=sfl(data.values.tolist()[w:-w]), name=title)


def get_sql_data(table, filter):
    with db.connect() as c:
        q = c.execute("select * FROM %s where %s " % (table, filter))
        return jsonify(result=q.cursor.fetchall())


def get_data(table):
    session_id = request.args.get("session_id")
    return get_sql_data(table, "session_id = '%s'" % session_id)


@app.route('/')
def hello_world():
    return app.send_static_file('index.html')


@app.route('/data/sessions')
def get_sessions():
    return get_sql_data("session_info", "1=1")


@app.route('/data/gps')
def get_gps_data():
    return get_data("gps_data")


@app.route('/data/imu')
def get_imu_data():
    return get_data("imu_data")


@app.route('/plot/accel')
def get_plot_timeseries():
    session_id = request.args.get("session_id")
    # TODO fail on bad session_id
    with db.connect() as c:
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
def get_gpsplot_timeseries():
    session_id = request.args.get("session_id")
    # TODO fail on bad session_id
    with db.connect() as c:
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
def get_singlerun_timeseries():
    session_id = request.args.get("session_id")
    if 'smooth' in request.args:
        smoothing_window = int(request.args.get("smooth"))
    else:
        smoothing_window = 2

    gps_data = pd.read_sql_query("select timestamp, speed, track, lat, lon FROM %s where session_id='%s'" % ("gps_data", session_id), db, index_col='timestamp')
    imu_data = pd.read_sql_query("select timestamp, x_accel, y_accel, z_accel FROM %s where session_id='%s'" % ("imu_data", session_id), db, index_col='timestamp')

    data = [
        get_scatterplot(gps_data.speed, smoothing_window, "Speed (avg)"),
        get_scatterplot(imu_data.z_accel, smoothing_window, "ZAccel (avg)")
    ]

    layout = pgo.Layout(
        title="Run",
        xaxis=dict(title="time"),
        yaxis=dict(title="value")
    )
    fig = pgo.Figure(data=data, layout=layout)
    return jsonify(data=fig.get('data'), layout=fig.get('layout'))


@app.route('/export/csv')
def get_run_csv():
    session_id = request.args.get("session_id")
    get_csv_cmd="""
select * from
(select
    session_id,timestamp,'GPS' as type,time,speed,track,lat,lon,epx,epy,epv,
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
    with db.connect() as c:
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
