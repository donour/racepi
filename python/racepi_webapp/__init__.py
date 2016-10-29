from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from plotly import graph_objs as pgo

app = Flask(__name__)
db = create_engine('sqlite:////home/donour/test.db')


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
    #return get_sql_data("sessions", "1=1")

    with db.connect() as c:
        q = c.execute(
            """
            select
                id, description, gps_count, imu_count
                from sessions as session
            join
                (select session_id,count(distinct timestamp) as imu_count from imu_data group by session_id) as imu
                on imu.session_id = session.id
            join
                (select session_id,count(distinct timestamp) as gps_count from gps_data group by session_id) as gps
                on gps.session_id = session.id
            """
        )
        return jsonify(result=q.cursor.fetchall())


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
        #q = c.execute("select timestamp,r,p,y FROM %s where %s " % ("imu_data", "session_id='%s'" % session_id))
        q = c.execute("select timestamp,x_accel,y_accel,z_accel FROM %s where %s " % ("imu_data", "session_id='%s'" % session_id))
        t = []
        x = []
        y = []
        z = []
        data = q.cursor.fetchall()
        t0 = data[0][0]
        map(lambda p: t.append(p[0]-t0), data)
        map(lambda p: x.append(p[1]), data)
        map(lambda p: y.append(p[2]), data)
        map(lambda p: z.append(p[3]), data)
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
