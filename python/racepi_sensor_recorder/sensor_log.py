#!/usr/bin/env python2

import numpy
import os, math, uuid, time
from multiprocessing import Queue, Event, Process
from pi_sense_hat_imu import record_from_imu
from gpsd import record_from_gps


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
    

if __name__ == "__main__":

    imu_handler = sensorHandler(record_from_imu)
    gps_handler = sensorHandler(record_from_gps)

    try:
        imu_handler.start()
        gps_handler.start()
    
        session_id = uuid.uuid1()
        print "New session: " + str(session_id)

        gps_sample = None
        while True:
            imu_data = imu_handler.get_all_data()
            gps_data = gps_handler.get_all_data()
            if imu_data:
                t = imu_data[0][0]
                pose = imu_data[0][1]['fusionPose']
                pose = map(math.degrees, pose)
                os.write(1, "\r[%.3f] %2.4f %2.4f %2.4f :: %s" % (
                    t,pose[0], pose[1], pose[2], str(gps_sample) ))

            if gps_data:
                gps_sample = gps_data

            if not imu_data and not gps_data:
                # empty queues, relieve the CPU a little
                time.sleep(0.01) # 
                    
                    
    except KeyboardInterrupt:
        imu_handler.stop()
        gps_handler.stop()
        print "done"
