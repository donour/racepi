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
    return get_sql_data("sessions", "1=1")


@app.route('/data/gps')
def get_gps_data():
    return get_data("gps_data")


@app.route('/data/imu')
def get_imu_data():
    return get_data("imu_data")


@app.route('/plot/timeseries')
def get_plot_timeseries():
    session_id = request.args.get("session_id")
    # TODO fail on bad session_id
    with db.connect() as c:
        q = c.execute("select time,speed FROM %s where %s " % ("gps_data", "session_id='%s'" % session_id))
        x = []
        y = []
        data = q.cursor.fetchall()
        map(lambda p: x.append(p[0]), data)
        map(lambda p: y.append(p[1]), data)
        data = [
            pgo.Scatter(x=x, y=y)
        ]
        layout = pgo.Layout(title="Timeseries")
        fig = pgo.Figure(data=data, layout=layout)
        return jsonify(result=fig)
