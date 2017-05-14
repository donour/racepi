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

# TODO: untested

import bluetooth as bt

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
            nearby_devices = bt.discover_devices(lookup_names=True, duration=2)
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

            print(d)
            # TODO, parse and post the data to the rx queue

        if self.sock:
            self.sock.close()


