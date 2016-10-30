#!/usr/bin/env python2

import gps, datetime, time, os


ALLOWED_DELTA_SECONDS=60*10

s = gps.gps(mode=gps.WATCH_ENABLE)

data = s.next()
while data is None or not 'time' in data.keys():
    data=s.next()

t = data["time"]
st = datetime.datetime.now()   
now = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ")
if abs((st-now).seconds) > ALLOWED_DELTA_SECONDS:
    os.system("date --s=%s" % t)
    print abs((st-now).seconds)
    print "Time delta to large, set time to:", t
else:
    print "Time within allowable range, exiting"





