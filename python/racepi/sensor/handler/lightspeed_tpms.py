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

import bluetooth as bt
from collections import defaultdict

import time

from racepi.sensor.handler.sensor_handler import SensorHandler

DEFAULT_TPMS_NAME = 'TPMS'
TPMS_BT_PORT = 6
TPMS_MSG_MARKER_BYTES = b'\x55\xAA'
TPMS_MESG_LEN = 40

TPMS_LOCATION_MAP = {
    0x00: 'lf',
    0x01: 'rf',
    0x10: 'lr',
    0x11: 'rr'
}
TPMS_LOCATION_MAP = defaultdict(str, TPMS_LOCATION_MAP)
TPMS_DATA_MESG_LEN = 8


class LightSpeedTPMSMessageParser:

    @staticmethod
    def __format_temp_c(val):
        return float(val) - 50

    @staticmethod
    def __format_pressure_bar(val):
        return float(val)*0.0344

    @staticmethod
    def _parse_data_sample(sample):
        result = None
        if sample and len(sample) >= TPMS_DATA_MESG_LEN - 2:
            size = sample[0]
            if size == TPMS_DATA_MESG_LEN:
                location = TPMS_LOCATION_MAP[sample[1]]
                pressure = LightSpeedTPMSMessageParser.__format_pressure_bar(sample[2])
                temp = LightSpeedTPMSMessageParser.__format_temp_c(sample[3])
                low_voltage = (sample[4] & 0x10) != 0
                signal_loss = (sample[4] & 0x20) != 0

                cksum = sample[5]
                # TODO, verify checksum

                result = {
                    'location': location,
                    'pressure': pressure,
                    'temp': temp,
                    'low_voltage': low_voltage,
                    'signal_loss': signal_loss,
                }
        return result

    @staticmethod
    def unpack_messages(byte_data):
        results = defaultdict(dict)
        data = byte_data.split(TPMS_MSG_MARKER_BYTES)
        for sample in data:
            if sample:
                r = LightSpeedTPMSMessageParser._parse_data_sample(sample)
                results[r['location']] = r
        return results


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
        self.sock = bt.BluetoothSocket(bt.RFCOMM)
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

            try:
                d = self.sock.recv(TPMS_MESG_LEN)
                now = time.time()
                data = LightSpeedTPMSMessageParser.unpack_messages(d)
                self.pipe_out.send((now, data))
            except bt.btcommon.BluetoothError:
                print("tpms: disconnected")
                self.sock = None

        if self.sock:
            self.sock.close()


