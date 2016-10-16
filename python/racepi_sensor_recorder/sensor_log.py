#!/usr/bin/env python2

import sqlite3
import os, uuid, time
from multiprocessing import Queue, Event, Process

from pi_sense_hat_imu import record_from_imu
import pi_sense_hat_display
from gpsd import record_from_gps

DB_LOCATION="/external/racepi_data/test.db"

class sensorHandler:
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

    
class dbHandler:
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

                os.write(1, "\r[%.3f] %2.4f %2.4f %2.4f" % (
                    t,pose[0], pose[1], pose[2]))

                insert_cmd = """
                  insert into imu_data
                  (session_id, timestamp,
                   r, p, y, x_accel, y_accel, z_accel)
                  values
                  ('%s', %s,
                   %f, %f, %f, %f, %f, %f)
                """ % (
                    (session_id.hex, t) +
                     tuple(pose) + tuple(accel))

                self.conn.execute(insert_cmd)

        if imu_data:
            self.conn.commit()
                

    
    def insert_gps_updates(self, gps_data, session_id):
        field_names = ['time','lat','lon','speed','track','epx','epy','epv']

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

    print "Opening Database"
    db_handler = dbHandler(DB_LOCATION)

    from sense_hat import SenseHat
    display = pi_sense_hat_display.RacePiStatusDisplay(SenseHat())
    
    print "Opening sensor handlers"
    display.set_col_init(pi_sense_hat_display.IMU_COL)
    imu_handler = sensorHandler(record_from_imu)

    display.set_col_init(pi_sense_hat_display.GPS_COL)
    gps_handler = sensorHandler(record_from_gps)
    
    try:
        imu_handler.start()
        display.set_col_ready(pi_sense_hat_display.IMU_COL)
        gps_handler.start()
        display.set_col_ready(pi_sense_hat_display.GPS_COL)
    
        session_id = db_handler.get_new_session()
        print "New session: " + str(session_id)

        gps_sample = None
        while True:
            imu_data = imu_handler.get_all_data()
            gps_data = gps_handler.get_all_data()

            db_handler.insert_gps_updates(gps_data, session_id)
            db_handler.insert_imu_updates(imu_data, session_id)
            
            if not imu_data and not gps_data:
                # empty queues, relieve the CPU a little
                time.sleep(0.01) #                     
                    
    except KeyboardInterrupt:
        imu_handler.stop()
        gps_handler.stop()
        print "done"
