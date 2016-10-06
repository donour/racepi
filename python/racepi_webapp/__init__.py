from flask import Flask, jsonify
from sqlalchemy import create_engine

app = Flask(__name__)
db = create_engine('sqlite:////home/donour/test.db')


def get_data(table):
    c = db.connect()
    q = c.execute("select * FROM %s" % table);
    return jsonify(result=q.cursor.fetchall())


@app.route('/')
def hello_world():
    return app.send_static_file('index.html')


@app.route('/sessions')
def get_sessions():
    return get_data("sessions")


@app.route('/gps')
def get_gps_data():
    return get_data("gps_data")


@app.route('/imu')
def get_imu_data():
    return get_data("imu_data")

