#!/usr/bin/env python2
# Copyright 2016 Donour Sizemore
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

import time, operator
from pi_sense_hat_imu import RpiImuSensorHandler
from gps_handler import GpsSensorHandler
from sqlite_handler import DbHandler
from can_handler import CanSensorHandler
from pi_sense_hat_display import RacePiStatusDisplay, GPS_COL, IMU_COL, CAN_COL

DEFAULT_DB_LOCATION = "/external/racepi_data/test.db"
MOVE_SPEED_THRESHOLD = 0.01

# TODO: make recorded can ids configurable
FORD_FOCUS_RS_CAN_IDS = ["010", "080", "213"]


class SensorLogger:

    def __init__(self, databaseLocation = DEFAULT_DB_LOCATION):
        print "Opening Database"
        self.db_handler = DbHandler(databaseLocation)
        print "Opening sensor handlers"
        self.display = RacePiStatusDisplay()
        self.imu_handler = RpiImuSensorHandler()
        self.gps_handler = GpsSensorHandler()
        self.can_handler = CanSensorHandler(FORD_FOCUS_RS_CAN_IDS)

    def start(self):

        self.imu_handler.start()
        self.gps_handler.start()
        self.can_handler.start()
        
        recording_active = False
        last_display_update_time = 0
        last_gps_update_time = 0
        last_imu_update_time = 0
        last_can_update_time = 0        

        try:
            while True:
                imu_data = self.imu_handler.get_all_data()
                gps_data = self.gps_handler.get_all_data()
                can_data = self.can_handler.get_all_data()

                if not imu_data and not gps_data and not can_data:
                    # empty queues, relieve the CPU a little
                    time.sleep(0.02)

                else:                
                    is_moving = reduce(operator.or_ ,
                        map(lambda s: s[1].get('speed') > MOVE_SPEED_THRESHOLD, gps_data), False)

                    # record whenever velocity != 0, otherwise stop
                    if is_moving and not recording_active:
                        session_id = self.db_handler.get_new_session()
                        print "New session: " + str(session_id)
                        recording_active = True

                    if not is_moving and gps_data:
                        recording_active = False

                    if recording_active:
                        try:
                            self.db_handler.insert_gps_updates(gps_data, session_id)
                            self.db_handler.insert_imu_updates(imu_data, session_id)
                            self.db_handler.insert_can_updates(can_data, session_id)
                        except TypeError as te:
                            print "Failed to insert data:", te

                # display update logic
                now = time.time()
                if gps_data:
                    last_gps_update_time = now
                if imu_data:
                    last_imu_update_time = now
                if can_data:
                    last_can_update_time = now

                self.display.refresh_display(last_gps_update_time,
                                             last_imu_update_time,
                                             last_can_update_time,
                                             recording_active)
        finally:
            self.gps_handler.stop()
            self.can_handler.stop()
            self.imu_handler.stop()
            
if __name__ == "__main__":
    sl = SensorLogger()
    sl.start()
