from flask import Flask, jsonify, request
from sqlalchemy import create_engine

app = Flask(__name__)
db = create_engine('sqlite:////home/donour/test.db')


def get_sql_data(table, filter):
    c = db.connect()
    q = c.execute("select * FROM %s where %s " % (table, filter));
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

