#!/usr/bin/env python2
"""
This is a tool for autocross performance data from multiple
sensor sources. Each sensor source implements a get_data() 
api runs in its own system process to allow for pre-emptive
scheduling and to limit contention for system resources.
"""

import sqlite3
import os, uuid, time, operator
from multiprocessing import Queue, Event, Process
from gpsd import GPS_REQUIRED_FIELDS

DB_LOCATION="/external/racepi_data/test.db"
MOVE_SPEED_THRESHOLD=3.5
DISPLAY_UPDATE_TIME=0.05

class SensorHandler:    
    """
    Base handler class for using producer-consumer sensor reading, using
    multiproccess
    """
    def __init__(self, read_func):
        self.doneEvent = Event()
        self.data_q = Queue()
        self.process = Process(target=read_func, args=(self.data_q, self.doneEvent))

    def start(self):
        self.process.start()

    def stop(self):
        self.doneEvent.set()
        self.process.join()

    def get_all_data(self):
        data = []
        while not self.data_q.empty():
            data.append(self.data_q.get())
        return data

    
class DbHandler:
    """
    Helper class for write to sqlite DB using RacePi schema
    """
    def __init__(self, db_location):
        
        self.conn = sqlite3.connect(db_location)
        if self.conn is None:
            raise IOError("Could not open db: " + db_location)
        self.conn.execute("PRAGMA foreign_keys = ON;");
        self.conn.execute("PRAGMA journal_mode=WAL;")
        
        
    def get_new_session(self):
        """
        Create new session entry in DB and return the 
        session ID.
        """
        session_id = uuid.uuid1()
        insert_cmd = """
        insert into sessions (id, description)
        values ('%s', 'Created by RacePi')
        """ % session_id.hex
        self.conn.execute(insert_cmd)
        return session_id

    
    def insert_imu_updates(self, imu_data, session_id):
        for sample in imu_data:
            if sample:
                t = sample[0]
                pose = sample[1]['fusionPose']
                accel= sample[1]['accel']
                gyro = sample[1]['gyro']

                #os.write(1, "\r[%.3f] %2.4f %2.4f %2.4f" % (
                #    t,pose[0], pose[1], pose[2]))

                insert_cmd = """
                  insert into imu_data
                  (session_id, timestamp,
                   r, p, y, x_accel, y_accel, z_accel, x_gyro, y_gyro, z_gyro)
                  values
                  ('%s', %s,
                   %f, %f, %f, %f, %f, %f, %f, %f, %f)
                """ % (
                    (session_id.hex, t) +
                     tuple(pose) + tuple(accel) + tuple(gyro))
                self.conn.execute(insert_cmd)

        if imu_data:
            self.conn.commit()
                

    def insert_gps_updates(self, gps_data, session_id):
        field_names = GPS_REQUIRED_FIELDS

        for sample in gps_data:
            # system time of sample
            t = sample[0]   
            # extract just the fields we use
            d = map(sample[1].get, field_names)
            available_fields = sample[1].keys()          

            # the sample is only usuable if it has velocity
            if 'speed' in available_fields:                
                insert_cmd = """
                  insert into gps_data
                  (session_id, timestamp,
                   %s)
                  values
                  ('%s', %s,
                   '%s', %f, %f, %f, %f, %f, %f, %f)
                """ % (
                    (','.join(field_names),
                    session_id.hex, t)  + tuple(d))
                self.conn.execute(insert_cmd)

        if gps_data:
            self.conn.commit()  


if __name__ == "__main__":

    # initialize sensor modules    
    from pi_sense_hat_imu import record_from_imu
    from gpsd import record_from_gps
    from elm327 import record_from_elm327
    import pi_sense_hat_display

    
    print "Opening Database"
    db_handler = DbHandler(DB_LOCATION)

    from sense_hat import SenseHat
    display = pi_sense_hat_display.RacePiStatusDisplay(SenseHat())
    
    print "Opening sensor handlers"
    imu_handler = SensorHandler(record_from_imu)
    gps_handler = SensorHandler(record_from_gps)
    obd_handler = SensorHandler(record_from_elm327)
    
    try:
        imu_handler.start()
        gps_handler.start()
        obd_handler.start()
    
        recording_active = False
        last_display_update_time = 0;
        last_gps_update_time = 0
        last_imu_update_time = 0        

        while True:
            imu_data = imu_handler.get_all_data()
            gps_data = gps_handler.get_all_data()

            if not imu_data and not gps_data:
                # empty queues, relieve the CPU a little
                time.sleep(0.01)

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
