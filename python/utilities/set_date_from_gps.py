#!/usr/bin/env python2
# Copyright 2016-7 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
"""
This is a hacked up script to set system time from GPS time 
without support for PPS or ntpd. Accuracy of the system clock
will typically be no better than ~1s.

Time is only set if the clock falls outside of a large, allowed
window. This is useful for resetting time on a system without
a RTC, like the Raspberry Pi.
"""
import gps, datetime, os

#TODO port to python3

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
    print(abs((st-now).seconds))
    print("Time delta to large, set time to:" + str(t))
else:
    print("Time within allowable range, exiting")





