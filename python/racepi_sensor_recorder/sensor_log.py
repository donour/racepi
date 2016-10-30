#!/usr/bin/env python2
"""
This is a tool for autocross performance data from multiple
sensor sources. Each sensor source implements a get_data() 
api runs in its own system process to allow for pre-emptive
scheduling and to limit contention for system resources.
"""

import os, time, operator
from multiprocessing import Queue, Event, Process
from gpsd import GPS_REQUIRED_FIELDS, GpsSensorHandler
from pi_sense_hat_imu import RpiImuSensorHandler
from sqlite_handler import DbHandler
from sense_hat import SenseHat
from pi_sense_hat_display import RacePiStatusDisplay, GPS_COL, IMU_COL

DEFAULT_DB_LOCATION="/external/racepi_data/test.db"
MOVE_SPEED_THRESHOLD=3.5
DISPLAY_UPDATE_TIME=0.05   


class SensorLogger:

    def __init__(self, databaseLocation = DEFAULT_DB_LOCATION):
        print "Opening Database"
        self.db_handler = DbHandler(databaseLocation)
        print "Opening sensor handlers"
        self.display = RacePiStatusDisplay(SenseHat())
        self.imu_handler = RpiImuSensorHandler()
        self.gps_handler = GpsSensorHandler()

    def start(self):
        self.imu_handler.start()
        self.gps_handler.start()
           
        recording_active = False
        last_display_update_time = 0;
        last_gps_update_time = 0
        last_imu_update_time = 0        

        while True:
            imu_data = self.imu_handler.get_all_data()
            gps_data = self.gps_handler.get_all_data()

            if not imu_data and not gps_data:
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
                    recording_active = False;                    

                if recording_active:
                    try:
                        self.db_handler.insert_gps_updates(gps_data, session_id)
                        self.db_handler.insert_imu_updates(imu_data, session_id)
                    except TypeError as te:
                        print "Failed to insert data: ", te

            # display update logic
            now = time.time()
            if gps_data:
                last_gps_update_time = now
            if imu_data:
                last_imu_update_time = now

            if now - last_display_update_time >  DISPLAY_UPDATE_TIME :
                if now - last_gps_update_time > 1:
                    self.display.set_col_init(GPS_COL)
                else:
                    self.display.set_col_ready(GPS_COL)
                if now - last_imu_update_time > 1:
                    self.display.set_col_init(IMU_COL)
                else:
                    self.display.set_col_ready(IMU_COL)
                last_display_update_time = now
                self.display.heartbeat()
                self.display.set_recording_state(recording_active)
        


if __name__ == "__main__":
    sl = SensorLogger()
    sl.start()
        
