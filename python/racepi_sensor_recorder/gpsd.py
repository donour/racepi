#!/usr/bin/env python2
import os
import gps
import time

BAUD_RATE="38400"
GPS_REQUIRED_FIELDS = ['time','lat','lon','speed','track','epx','epy','epv']
 
def record_from_gps(q, done):

    if not q:
        raise ValueError("Illegal argument, no queue specified")

    session = gps.gps(mode = gps.WATCH_ENABLE)
    while not done.is_set():
        while not session:
            # set baudrate for serial gps receiver
            if os.path.isfile('/dev/gpsm8n'):
                os.system("stty -F /dev/gpsm8n ispeed " + BAUD_RATE)
                session = gps.gps(mode = gps.WATCH_ENABLE)
            
        data = session.next()
        t = data.get('time')
        if t is not None and set(GPS_REQUIRED_FIELDS).issubset(set(data.keys())):
            q.put( (time.time(), data))


if __name__ == "__main__":
    from multiprocessing import Queue, Event, Process

    done = Event()
    q = Queue()

    p = Process(target=record_from_gps, args=(q,done))
    p.start()
    while True:
        print q.get()


    

