# Copyright 2017-8 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

import time
import socket
from math import pi
from collections import defaultdict
from threading import Event, Thread

from racepi.can.data import CanFrame
from racepi.can import \
    focus_rs_tps_converter, focus_rs_rpm_converter, \
    focus_rs_steering_angle_converter, focus_rs_steering_direction_converter, \
    lotus_evora_s1_rpm_converter, lotus_evora_s1_steering_angle_converter, lotus_evora_s1_tps_converter
from racepi.sensor.data_utilities import safe_speed_to_float
from racepi.racetech.messages import *

DL1_ANALOG_MAX_VOLTAGE = 5.0
MAX_BRAKE_PRESSURE = float(1e-6)  # TODO determine proper unit

# Occasionally, the can bus (or sensor) will spit out absurd steering angle values
# for a second or too. This happened on both the FocusRS and Evora. The writer
# will clip these values if their magnitude is greater than a threshold.
CLIP_STEERING_ANGLE = 720.0  # degrees

# Some sensors are rate limited
MIN_SAMPLE_INTERVAL = 0.05  # 20 hz
last_sample_time = defaultdict(int)


class RaceTechnologyDL1FeedWriter:

    def __init__(self):
        self.__socket_listener_done = Event()
        self.__active_connections = []
        self.pending_messages = []

        # open and bind RFCOMM listener
        self.__socket_listener_thread = \
            Thread(target=RaceTechnologyDL1FeedWriter.__bind_rfcomm_socket,
                   args=(self.__socket_listener_done, self.__active_connections))
        self.__socket_listener_thread.setDaemon(True)
        self.__socket_listener_thread.start()

        self.__earliest_time_seen = time.time()

    def close(self):
        self.__socket_listener_done.set()

    def number_of_clients(self):
        return len(self.__active_connections)

    @staticmethod
    def __bind_rfcomm_socket(done_event, clients):

        mac = '0:0:0:0:0:0'
        port = 1
        backlog = 1
        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        s.bind((mac, port))
        s.listen(backlog)
        while not done_event.is_set():
            client, addr = s.accept()
            print("Registering: %s" % str(addr))
            clients.append(client)

        for c in clients:
            c.close()
        s.close()

    def __queue_mesg(self, msg):
        self.pending_messages.append(msg)

    def flush_queued_messages(self):
        if not self.pending_messages:
            return

        # join each message with its checksum, then
        # join all data together into a bulk message
        msg = b"".join(
            [b"".join([x, get_message_checksum(x)]) for x in self.pending_messages])
        
        self.pending_messages = []

        # write to all open RFCOMM connections
        for client in self.__active_connections:
            try:
                client.send(msg)
            except ConnectionResetError:
                # connection terminated
                self.__active_connections.remove(client)
                client.close()

    def send_timestamp(self, timestamp_seconds):
        if not timestamp_seconds:
            return

        time_delta = timestamp_seconds - self.__earliest_time_seen
        # supposed to be millis, isn't really
        msg = get_timestamp_message_bytes(time_delta * 100.0)
        self.__queue_mesg(msg)

    def send_gps_speed(self, speed):
        if not speed:
            return

        msg = get_gps_speed_message_bytes(speed*100.0)
        self.__queue_mesg(msg)

    def send_gps_pos(self, lat, lon, err):        

        # missing position data is a no-op
        if not lat or not lon:
            return

        try:
            lat_val = float(lat)
            lon_val = float(lon)
        except ValueError as e:
            return

        # missing error data is ignored
        try:
            err_val = float(err)
        except ValueError as e:
            err_val = 0.0       

        msg = get_gps_pos_message_bytes(lat_val * float(1e7), lon_val * float(1e7), err_val*1000.0)
        self.__queue_mesg(msg)

    def send_xyz_accel(self, x_accel, y_accel, z_accel):
        msg = get_xy_accel_message_bytes(x_accel, y_accel)
        self.__queue_mesg(msg)
        msg = get_z_accel_message_bytes(z_accel)
        self.__queue_mesg(msg)

    def send_rpm(self, rpm):
        msg = get_rpm_message_bytes(rpm)
        self.__queue_mesg(msg)

    def send_tps(self, tps_percentage):
        msg = get_tps_message_bytes(tps_percentage/100.0*DL1_ANALOG_MAX_VOLTAGE)
        self.__queue_mesg(msg)

    def send_brake_pressure(self, brake_pressure):
        msg = get_ext_pressure_message_bytes(brake_pressure)
        self.__queue_mesg(msg)
        msg = get_brake_pressure_message_bytes(brake_pressure)
        self.__queue_mesg(msg)

    def send_steering_angle(self, angle):
        # send value only if it is within the allowable range
        if -CLIP_STEERING_ANGLE < angle < CLIP_STEERING_ANGLE:
            msg = get_steering_angle_message_bytes(angle)
            self.__queue_mesg(msg)

    def write_gps_sample(self, timestamp, data):
        """
        
        :param timestamp: 
        :param data: 
        :return: 
        """
        self.send_timestamp(timestamp)
        self.send_gps_speed(safe_speed_to_float(data.get('speed')))
        lat = data.get('lat')
        lon = data.get('lon')
        err = data.get('epy')
        
        if type(lat) is float:
            self.send_gps_pos(lat, lon, err)

    def write_imu_sample(self, timestamp, data):
        """
        Write IMU data to Racetech data clients
        :param timestamp: 
        :param data: dictionary of accel and gyro data
        """
        accel = data.get('accel')
        if not accel:
            return

        self.send_timestamp(timestamp)
        self.send_xyz_accel(accel[0], accel[1], accel[2])
        #TODO write gyro data

    def write_can_sample(self, timestamp, data):
        """
        Write an unprocessed can sample to Racetech data clients

        :param timestamp: timestamp of the can message
        :param data: unprocesses can data as byte array
        :raises: ValueError if can message is unprocessable
        """

        if len(data) < 5:
            return  # skip

        arb_id = data[:3]
        payload = data[3:]

        if (timestamp - last_sample_time[arb_id]) < MIN_SAMPLE_INTERVAL:
            return  # skip, rate limit
        else:
            last_sample_time[arb_id] = timestamp

        frame = CanFrame(arb_id, payload)

        # Focus RS MK3 Messages
        if arb_id == "010":
            direction = focus_rs_steering_direction_converter.convert_frame(frame)
            angle = focus_rs_steering_angle_converter.convert_frame(frame)
            if direction > 0:
                angle = -angle
            angle *= 180.0 / pi  # radians -> degrees
            self.send_timestamp(timestamp)
            self.send_steering_angle(angle)

        if arb_id == "080":
            tps = focus_rs_tps_converter.convert_frame(frame)
            self.send_timestamp(timestamp)
            self.send_tps(tps)

        if arb_id == "090":
            rpm = focus_rs_rpm_converter.convert_frame(frame)
            self.send_timestamp(timestamp)
            self.send_rpm(rpm)

        #  Brake pressure messages do not currently work
        #  if arb_id == "213":
        #    pressure = focus_rs_brake_pressure_converter.convert_frame(frame)
        #    self.send_timestamp(timestamp)
        #    self.send_brake_pressure(pressure)

        # Evora Messages
        if arb_id == "085":
            angle = lotus_evora_s1_steering_angle_converter.convert_frame(frame)
            self.send_timestamp(timestamp)
            self.send_steering_angle(angle)

        if arb_id == "114":
            tps = lotus_evora_s1_tps_converter.convert_frame(frame)
            self.send_timestamp(timestamp)
            self.send_tps(tps)

        if arb_id == "400":
            rpm = lotus_evora_s1_rpm_converter.convert_frame(frame)
            self.send_timestamp(timestamp)
            self.send_rpm(rpm)
