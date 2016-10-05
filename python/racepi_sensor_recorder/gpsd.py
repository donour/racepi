#!/usr/bin/env python2
import os
import gps
import time

def record_from_gps(q, done):

    if not q:
        raise ValueError("Illegal argument, no queue specified")

    session = gps.gps(mode = gps.WATCH_ENABLE)
    while not done.is_set():
        data = session.next()
        t = data.get('time')
        s = data.get('speed')
        track = data.get('track')
        lat = data.get('lat')
        lon = data.get('lon')
        if t is not None:
            q.put( (time.time(), data))

if __name__ == "__main__":
    from multiprocessing import Queue, Event, Process

    done = Event()
    q = Queue()

    p = Process(target=record_from_gps, args=(q,done))
    p.start()
    while True:
        print q.get()


    

