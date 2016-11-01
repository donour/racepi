#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
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
"""
Library for communicating with STN11xx device via a serial
port. This includes the STN1130 and STN1170 inside OBDLink
devices such as the OBDLink SX. It does not currently
support network connections, so it cannot communication
with WiFi bridged devices such as the OBDLink MX.
"""

import serial
import time

BAUD_RATE = "576000"
DEV_NAME = "/dev/obdlink"
FORCE_PROTOCOL = 6
ST_PROTOCOL = 33
RESET_WAIT_TIME_SECONDS = 6.0

class STNHandler:

    def __init__(self, dev=DEV_NAME, baud=BAUD_RATE):

        print "Initializing STN11xx device on port", dev
        # TODO autoset baudrate
        self.port = serial.Serial(dev, baud)
        if dev != self.port.getPort():
            raise IOError("Could not open" + dev)

        # reset device and wait for startup
        self.__send_command('atz')
        time.sleep(RESET_WAIT_TIME_SECONDS)
        self.port.read()  # empty buffer

        self.get_sample("ATE0")        # command echo
        self.__run_config_cmd("ATL0")  # line breaks
        self.__run_config_cmd("ATS0")  # whitespace
        self.__run_config_cmd("ATAL")  # long messages
        self.__run_config_cmd("ATH1")  # headers

        self.elm_version = self.get_sample('ati')
        self.stn_version = self.get_sample('sti')
        self.dev_description = self.get_sample('at@1')

        # ensure device is ELM compatible
        if not 'ELM327' in self.elm_version:
            raise IOError("Failed to find ELM device")
        # ensure device is STN11xx compatible
        if not 'stn11' in self.stn_version.lower():
            raise IOError("Failed to find STN11xx device: " + self.stn_version )

        print "Found device:", self.stn_version
        
        # set manual protocol selection
        self.__run_config_cmd("stp " + str(ST_PROTOCOL))
        self.__run_config_cmd("atsp " + str(FORCE_PROTOCOL))

        # clear CAN filters and block all messages
        self.set_monitor_ids(None)

    def set_monitor_ids(self, ids):
        """
        Reset CAN monitors to only allow data from the list
        of CAN IDs specified in ids
        """
        self.__run_config_cmd("stfcp")
        self.__run_config_cmd("stfcb")
        self.__run_config_cmd("stfab FFF,FFF")
        if ids:
            for can_id in ids:
                self.__run_config_cmd("stfap %s,FFF" % can_id)

    def __run_config_cmd(self, cmd):
        r = self.get_sample(cmd)
        print cmd, r
        if 'ok' not in r.lower():
            raise IOError("Failed to run cmd: "+cmd)
    
    def get_is_connected(self):
        """
        Determine if the device is still connected by checking if the ID string
        is the same as during init
        """
        return self.elm_version in self.get_sample('ati')
    
    def get_is_plugged_in(self):
        """
        Determine if the device is plugged into a vehicle by checking the 
        voltage pin reading
        """
        response = self.get_sample('atrv')
        if '0.0V' == response:
            return False
        return True

    def get_sample(self, cmd):
        """
        Send a single ELM AT command and return the one line result
        """
        self.__send_command(cmd)
        time.sleep(0.2) # *sigh* i hate hardware, but i hate python hardware libraries more
        return self.__get_result()
        
    def __send_command(self, cmd):
        if self.port:
            self.port.flushOutput()
            self.port.flushInput()
            for c in cmd:
                self.port.write(c)
            self.port.write("\r")

    def start_monitor(self):
        """
        Set the device to monitor mode
        """
        self.__send_command("stm")

    def stop_monitor(self):
        """
        Disable device monitor mode
        """
        self.get_sample('ati')

    def readline(self):
        """
        Read a line of output from device. This is useful when
        monitoring the CAN bus.
        :return: single line of output, such as a CAN message
        """
        return self.__get_result()

    def __get_result(self):         
        if self.port:
            buf = ''
            while True:
                c = self.port.read(1)
                if c == '\r' and len(buf) > 0:
                    break
                else:
                    # if something is in buffer, add everything
                    if buf != '' or c != ">":
                        buf = buf + c

            if "no data" in buf.lower():
                return None                            
            return buf
        else:
            return None
                                                                                     

if __name__ == "__main__":
    import time, sys, os

    if len(sys.argv) < 2:
        print "Usage: %s <CAN ID> <CAN ID> ..." % sys.argv[0]
        sys.exit(1)

    sh = STNHandler(DEV_NAME, BAUD_RATE)
    # setup monitor of specified IDs
    last_mesg = {}
    for can_id in sys.argv[1:]:
        last_mesg[can_id] = None
    sh.set_monitor_ids(last_mesg.keys())

    sh.start_monitor()
    last_update = 0
    while True:
        # read all the messages that are available
        data = sh.readline()
        if len(data) > 3:
            can_id = data[:3]
            if can_id in last_mesg.keys():
                last_mesg[can_id] = data            

        now = time.time()
        if now - last_update > 0.2:
            last_update = now
            os.write(1, "\r")
            for k in last_mesg.keys():
                os.write(1, "[%s] " % last_mesg[k])
