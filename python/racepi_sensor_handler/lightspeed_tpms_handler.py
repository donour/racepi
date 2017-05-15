#!/usr/bin/env python3
# Copyright 2017 Donour Sizemore
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
"""
This sensor module supports the bluetooth TPMS sensors from Lightspeed/Macsboost.
http://macsboost.com/motorsports/data-acquisition/tpms/lightspeed-tpms-by-macsboost.html
"""

# Voltage query message
# (0x55, 0xAA, 0x6, 0x2, 0x1, 0xFA)
# GET_RESP_ID_SWITCH
#        byte[] bArr = new byte[6];
#        bArr[0] = (byte) 85;
#        bArr[1] = (byte) -86;
#        bArr[2] = (byte) 6;
#        bArr[3] = (byte) 2;
#        bArr[5] = (byte) -5;

# TireStat Format: 8bytes
# 1: 85
# 2: 170
# 3: 8
# 4: sensor ID
# 5: pressure, 68 ~= 33 psi ~= 233 kPA, 71 ~= 244 kPA ~= 35.39 psi,  value*256 * 8.8 = bar
# 6: temp, Celcius, value - 50
# 7: 0
# 8: unknown

# TODO: untested

import bluetooth as bt
from collections import defaultdict

import time

from .sensor_handler import SensorHandler

DEFAULT_TPMS_NAME = 'TPMS'
TPMS_BT_PORT = 6
TPMS_MESG_LEN = 40


class LightSpeedTPMSSensorHandler(SensorHandler):

    def __init__(self, tpms_name=DEFAULT_TPMS_NAME, bt_port=TPMS_BT_PORT):
        SensorHandler.__init__(self, self.__record_tpms)
        self.tpms_name = tpms_name
        self.port = bt_port
        self.sock = None

    def __connect(self):
        """
        Search for TPMS device and connect to the RFCOMM service on
        port 6.
        :return: 
        """
        dev_addr = None
        while not dev_addr:
            nearby_devices = bt.discover_devices(lookup_names=True)
            for addr, name in nearby_devices:
                if self.tpms_name in name:
                    print("tpms: %s - %s" % (addr, name))
                    dev_addr = addr

        # Create the client socket
        self.sock = bt.BluetoothSocket(bt.RFCOMM )
        self.sock.connect((dev_addr, self.port))

    def __record_tpms(self):
        if not self.pipe_out:
            raise ValueError("Illegal argument, no queue specified")

        print("Starting LightSpeed TPMS reader")
        while not self.doneEvent.is_set():
            if not self.sock:
                try:
                    self.__connect()
                except OSError as e:
                    print("tpms: failed to scan BT devices:" + str(e))
                    return

            d = self.sock.recv(TPMS_MESG_LEN)
            now = time.time()
            data = LightSpeedTPMSSensorHandler.__unpack_message(d)
            print(d)  # TODO, remove me
            self.pipe_out.send((now, data))

        if self.sock:
            self.sock.close()

    @staticmethod
    def __unpack_message(msg):
        # LS TPMS update messages contains 40 bytes
        return {
            'fl': LightSpeedTPMSSensorHandler.__extract_fields(msg[0:8]),
            'fr': LightSpeedTPMSSensorHandler.__extract_fields(msg[8:16]),
            'rl': LightSpeedTPMSSensorHandler.__extract_fields(msg[16:24]),
            'rr': LightSpeedTPMSSensorHandler.__extract_fields(msg[24:32])
        }

    @staticmethod
    def __extract_fields(data):
        result = defaultdict(float)
        result['temp'] = LightSpeedTPMSSensorHandler.__format_temp_c(data[5])
        result['pressure'] = LightSpeedTPMSSensorHandler.__format_pressure_bar(data[4])
        return result

    @staticmethod
    def __format_temp_c(val):
        return float(val) - 50

    @staticmethod
    def __format_pressure_bar(val):
        return float(val)/256.0 * 8.8


