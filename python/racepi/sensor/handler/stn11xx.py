#!/usr/bin/env python3
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

GREEN = '\033[92m'
ENDC = '\033[0m'
BOLD = '\033[1m'


class STNHandler:

    def __init__(self, dev=DEV_NAME, baud=BAUD_RATE, headers=True):

        # TODO autodetect and set baudrate
        # TODO auto retry and reinit on hotplug
        print("Initializing STN11xx device on port %s" % dev)
        self.headers = headers
        self.port = serial.Serial(dev, baud)

        # reset device and wait for startup
        self.__send_command('atz')
        time.sleep(RESET_WAIT_TIME_SECONDS)
        self.port.read()  # empty buffer

        self.get_sample("ATE0")        # command echo
        self.__run_config_cmd("ATL0")  # line breaks
        self.__run_config_cmd("ATS0")  # whitespace
        self.__run_config_cmd("ATAL")  # long messages
        if self.headers:
            self.__run_config_cmd("ATH1")  # headers
        else:
            self.__run_config_cmd("ATH0")  # headers

        self.elm_version = self.get_sample('ati')
        self.stn_version = self.get_sample('sti')
        self.dev_description = self.get_sample('at@1')

        # ensure device is ELM compatible
        if 'ELM327' not in self.elm_version:
            raise IOError("Failed to find ELM device")
        # ensure device is STN11xx compatible
        if 'stn11' not in self.stn_version.lower():
            raise IOError("Failed to find STN11xx device: " + self.stn_version )

        print("Found device: %s" % self.stn_version)
        
        # set manual protocol selection
        self.__run_config_cmd("stp " + str(ST_PROTOCOL))
        self.__run_config_cmd("atsp " + str(FORCE_PROTOCOL))
        
    def set_monitor_ids(self, ids):
        """
        Reset CAN monitors to only allow data from the list
        of CAN IDs specified in ids
        """

        # TODO: these can_ids will need to be converted to strings
        # to work; passing in ints will fail

        self.__run_config_cmd("stfcp")
        self.__run_config_cmd("stfcb")
        self.__run_config_cmd("stfab FFF,FFF")
        if ids:
            for can_id in ids:
                self.__run_config_cmd("stfap %03x,FFF" % can_id)

    def __run_config_cmd(self, cmd):
        r = self.get_sample(cmd)
        print("STN11XX: %s\t=> %s" %
              (GREEN+cmd+ENDC, BOLD+r+ENDC))
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
        time.sleep(0.2)  # *sigh* i hate hardware, but i hate python hardware libraries more
        return self.__get_result()
        
    def __send_command(self, cmd):
        if self.port:
            self.port.flushOutput()
            self.port.flushInput()
            for c in cmd:
                self.port.write(c.encode())
            self.port.write("\r".encode())

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

    def get_pid(self, mode, pid):
        """
        Get a single OBD2 parameter id
        :param mode: J1979 mode id as string
        :param pid:  J1979 parameter id as string
        :return: result
        """
        self.__send_command(mode+pid)
        # TODO, headers should be checked and stripped here
        return self.__get_result()

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
                c = self.port.read(1).decode()
                if c == "\r" and len(buf) > 0:
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
