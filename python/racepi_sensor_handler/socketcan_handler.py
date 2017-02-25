#!/usr/bin/env python3
# Copyright 2016-7 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

import socket
import time
import struct
import platform

from .sensor_handler import SensorHandler

if not hasattr(socket, "PF_CAN"):
    raise RuntimeError("No SocketCAN support found: please use Python3.3+")

DEFAULT_CAN_DEVICE = "slcan0"

# Basic data frame format: https://en.wikipedia.org/wiki/CAN_bus#Data_frame
CAN_MESSAGE_FMT = "<IB3x8B"


class SocketCanSensorHandler(SensorHandler):

    def __init__(self, device_name=DEFAULT_CAN_DEVICE, can_filters=[]):
        """
        :param device_name: name of socketcan device (e.g. slcan0)
        :param can_filters: list of allowed arbitration IDs, as integer
        """
        SensorHandler.__init__(self, self.__record_from_can)
        self.dev_name = device_name
        self.cansocket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self._set_can_id_filters(can_filters)
        self.cansocket.bind((self.dev_name,))

    def _set_can_id_filters(self, can_filters):
        """
        Set RX filters to receive only specified IDs

        :param can_filters: list of arbitration IDs to receive
        """
        filter_fmt = "={}I".format(2 * len(can_filters))
        filter_data = []
        for f in can_filters:
            filter_data.append(f)
            filter_data.append(0xFFF)
            print("setting filter: %s" % str(f))
        self.cansocket.setsockopt(socket.SOL_CAN_RAW, socket.CAN_RAW_FILTER,
                                  struct.pack(filter_fmt, *filter_data))

    def __record_from_can(self):

        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        message_size = struct.calcsize(CAN_MESSAGE_FMT)

        print("Starting Socket-CAN reader")
        while not self.doneEvent.is_set():
            data = self.cansocket.recv(message_size)
            now = time.time()
            if data:

                # this unpacking is not strictly necessary, but is a nice
                # convention and adopted by most socketcan handlers
                data = struct.unpack(CAN_MESSAGE_FMT, data)

                # check for empty data
                if data and len(data) > 1:
                    # pack the message back into a string
                    result = "%03x" % data[0] + \
                             "".join([("%02x" % v) for v in data[2:]])
                    self.pipe_out.send((now, result))

        print("Shutting down CAN reader")

