#!/usr/bin/env python3
# Copyright 2016-8 Donour Sizemore
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
This is a tool for recording autocross performance data
from multiple sensor sources. Each sensor source implements
a get_data() api runs in its own system process to allow
for pre-emptive scheduling and to limit contention for
system resources.
"""

import time
import os
from enum import Enum
from collections import defaultdict

from racepi.sensor.data_utilities import merge_and_generate_ordered_log, safe_speed_to_float
from racepi.racetech.writers import RaceTechnologyDL1FeedWriter
from racepi.sensor.recorder.pi_sense_hat_display import RacePiStatusDisplay, SenseHat
from racepi.sensor.recorder.data_buffer import DataBuffer

ACTIVATE_RECORDING_M_PER_S = 9.5
MOVEMENT_THRESHOLD_M_PER_S = 2.5
DEFAULT_DATA_BUFFER_TIME_SECONDS = 10.0


class LoggerState(Enum):
    initialized = 1
    ready = 2
    logging = 3
    done = 4


class SensorLogger:
    """
    Main control logic for logging and writing to database

    The logger relies on GPS speed data for activating and deactivating
    sessions. Without GPS speed data, a manual trigger is required.

    The logger can be in the following states:

    initialized: configured sensors are ready for logging
    ready: sensor ready and actively buffered
    logging: actively logging data to the database
    done: logging is no longer possible
    """

    def __init__(self, db_handler, sensor_handlers={}):
        """
        Create new logger instance with specified handlers. Input and output
        handlers are required.

        :param db_handler: output handler for writing sensor data to a database
        :param sensor_handlers: input data handlers, these should be racepi sensor_handlers
        """

        # pin the main logging thread to the first cpu
        os.system("taskset -p 0x01 %d" % os.getpid())
        self.data = DataBuffer()
        self.display = None
        if SenseHat:
            self.display = RacePiStatusDisplay()        

        self.handlers = sensor_handlers
        self.db_handler = db_handler
        try:
            self.db_handler.connect()
        except Exception as e:
            print(e)
            print("No database handler available, recording disabled")
            self.db_handler = None

        self.session_id = None
        self.racetech_feed_writer = RaceTechnologyDL1FeedWriter()
        self.state = LoggerState.initialized

    def get_new_data(self):
        """
        Get dictionary of new data from all handlers and
        add all data to the current buffer
        :return: data dictionary
        """
        new_data = defaultdict(list)
        for h in self.handlers:
            new_data[h] = self.handlers[h].get_all_data()
            self.data.add_sample(h, new_data[h])
        return new_data

    def activate_conditions(self, data):
        """
        Determine whether recording should be activated based on this
        sample of data
        :param data:
        :return: true if activation conditions exist else false
        """

        # we cannot record without a DB destination
        if not self.db_handler:
            return False

        if not data or 'gps' not in data:
            return False

        # look for any sample above the speed threshold
        return True in \
            [safe_speed_to_float(s[1].get('speed')) > ACTIVATE_RECORDING_M_PER_S
             for s in data['gps']]

    def deactivate_conditions(self, data):
        """
        Determine whether recording should be de-activated based on this
        sample of data
        :param data:
        :return: true if de-activation conditions exist else false
        """
        if not data or 'gps' not in data:
            return False

        # loop for any sample above threshold, true only if there are none
        return True not in \
            [safe_speed_to_float(s[1].get('speed')) > MOVEMENT_THRESHOLD_M_PER_S
             for s in data['gps']]

    def write_data_rc_feed(self, data):
        """
        This function merges multiple data sources in time order
        """
        flat_data = merge_and_generate_ordered_log(data)
        for val in flat_data:
            if val:
                if val[0] == 'gps':
                    self.racetech_feed_writer.write_gps_sample(val[1], val[2])
                elif val[0] == 'imu':
                    self.racetech_feed_writer.write_imu_sample(val[1], val[2])
                elif val[0] == 'can':
                    try:  # handle crazy or unexpected messages from the can bus
                        self.racetech_feed_writer.write_can_sample(val[1], val[2])
                    except ValueError:
                        pass  # TODO log exceptions on can handling
        self.racetech_feed_writer.flush_queued_messages()

    def process_new_data(self, data):
        """
        Process dictionary of new data, change recording state if necessary
        and manage recording buffers.

        :param data: dict of sample lists from different SensorHandlers
        """
        if not data:
            return  # no-op

        # send all data to RaceCapture recorder if available
        self.write_data_rc_feed(data)

        # if necessary, transition state
        if self.state == LoggerState.ready:
            if self.activate_conditions(data):
                # ready -> logging
                self.session_id = self.db_handler.get_new_session()
                print("New session: %s" % str(self.session_id))
                self.state = LoggerState.logging
        elif self.state == LoggerState.logging:
            if self.deactivate_conditions(data):
                # logging -> ready
                self.state = LoggerState.ready
                # populate metadata for recently ended session
                if self.session_id:
                    # TODO, this session info population blocks the main thread for too
                    # long. It needs to be in a separate thread or process to keep remote
                    # data clients from losing their minds.
                    #
                    # self.db_handler.populate_session_info(self.session_id)
                    self.session_id = None
        else:
            raise RuntimeError("Invalid logger state:" + str(self.state))

        # process data based on current state

        if self.state == LoggerState.ready:
            self.data.expire_old_samples(time.time() - DEFAULT_DATA_BUFFER_TIME_SECONDS)

        elif self.state == LoggerState.logging:
            # write all buffered data to the db
            # TODO: change do a single insert/transaction
            if self.db_handler:
                try:
                    self.db_handler.insert_gps_updates(self.data.get_sensor_data('gps'), self.session_id)
                    self.db_handler.insert_imu_updates(self.data.get_sensor_data('imu'), self.session_id)
                    self.db_handler.insert_can_updates(self.data.get_sensor_data('can'), self.session_id)
                    # TODO workout whether TPMS data makese sense to keep
                    # self.db_handler.insert_tpms_updates(self.data.get_sensor_data('tpms'), self.session_id)
                except TypeError as te:
                    print("Failed to insert data: %s" % te)
            self.data.clear()

    def start(self):
        """
        Start handlers and begin recording. The function does not
        normally terminate. New sessions are created as needed.
        """
        for h in self.handlers.values():
            h.start()

        update_times = defaultdict(int)
        self.state = LoggerState.ready

        try:
            while True:
                # read new data
                new_data = self.get_new_data()
                # process data
                self.process_new_data(new_data)

                # update display
                for h in self.handlers:
                    if new_data[h]:
                        update_times[h] = new_data[h][-1][0]

                if self.display:
                    self.display.refresh_display(time.time() if self.db_handler else 0,
                                                 gps_time=update_times['gps'],
                                                 imu_time=update_times['imu'],
                                                 can_time=update_times['can'],
                                                 tire_time=0,  # update_times['tpms'],
                                                 recording=(self.state == LoggerState.logging))

                # there is no reason to ever poll faster than this
                # 20hz is generally faster than you need refresh remote
                # receivers
                time.sleep(0.05)
 
        finally:
            self.racetech_feed_writer.close()
            for h in self.handlers.values():
                h.stop()
