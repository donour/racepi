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

DEFAULT_DB_LOCATION="/external/racepi_data/test.db"
MOVE_SPEED_THRESHOLD=3.5
DISPLAY_UPDATE_TIME=0.05   

if __name__ == "__main__":

    # initialize sensor modules    
    from elm327 import record_from_elm327
    import pi_sense_hat_display
    
    print "Opening Database"
    db_handler = DbHandler(DEFAULT_DB_LOCATION)

    from sense_hat import SenseHat
    display = pi_sense_hat_display.RacePiStatusDisplay(SenseHat())
    
    print "Opening sensor handlers"
    imu_handler = RpiImuSensorHandler()
    gps_handler = GpsSensorHandler()

    try:
        imu_handler.start()
        gps_handler.start()
           
        recording_active = False
        last_display_update_time = 0;
        last_gps_update_time = 0
        last_imu_update_time = 0        

        while True:
            imu_data = imu_handler.get_all_data()
            gps_data = gps_handler.get_all_data()

            if not imu_data and not gps_data:
                # empty queues, relieve the CPU a little
                time.sleep(0.02)

            else:
                is_moving = reduce(operator.or_ ,
                              map(lambda s: s[1].get('speed') > MOVE_SPEED_THRESHOLD, gps_data), False)

                # record whenever velocity != 0, otherwise stop
                if is_moving and not recording_active:
                    session_id = db_handler.get_new_session()
                    print "New session: " + str(session_id)
                    recording_active = True

                if not is_moving and gps_data:
                    recording_active = False;                    

                if recording_active:
                    try:
                        db_handler.insert_gps_updates(gps_data, session_id)
                        db_handler.insert_imu_updates(imu_data, session_id)
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
                    display.set_col_init(pi_sense_hat_display.GPS_COL)
                else:
                    display.set_col_ready(pi_sense_hat_display.GPS_COL)
                if now - last_imu_update_time > 1:
                    display.set_col_init(pi_sense_hat_display.IMU_COL)
                else:
                    display.set_col_ready(pi_sense_hat_display.IMU_COL)
                last_display_update_time = now
                display.heartbeat()
                display.set_recording_state(recording_active)


    except KeyboardInterrupt:
        print "Keyboard exit"
    finally:
        imu_handler.stop()
        gps_handler.stop()
