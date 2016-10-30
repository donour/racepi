#!/usr/bin/env python2
import time
from sensor_handler import SensorHandler
from stn11xx import STNHandler

FORD_FOCUS_RS_CAN_IDS = ["010", "080", "213"]


class CanSensorHandler(SensorHandler):

    def __init__(self, can_ids = FORD_FOCUS_RS_CAN_IDS):
        SensorHandler.__init__(self, self.__record_from_canbus)
        self.stn = STNHandler()
        self.stn.set_monitor_ids(can_ids)
        
    def __record_from_canbus(self):
        """
        """

        if not self.data_q:
            raise ValueError("Illegal argument, no queue specified")

        self.stn.start_monitor()
        while not self.doneEvent.is_set():
            data = self.stn.readline()
            now = time.time()
            self.data_q.put( (now, data) )
            
        self.stn.get_sample('ati') # stop monitors

if __name__ == "__main__":

    sh = CanSensorHandler()
    sh.start()
    while True:
        data = sh.get_all_data()
        if data:
            print data
