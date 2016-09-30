#!/usr/bin/env python2

import sqlite3
import sys, os, time
import RTIMU

DB_LOCATION="/external/racepi_data/test.db"

conn = sqlite3.connect(DB_LOCATION)
if conn is None:
    print "Failed connecting to db: " + DB_LOCATION
    sys.exit(1)
else:
    print "Opened " + DB_LOCATION

def db_insert(c, r, p , y, x_accel, y_accel, z_accel):
    t = time.time()
    id = 1
    c.execute (
        """
        insert into imu_data
        (id, timestamp, 
         r, p, y,
         x_accel, y_accel, z_accel)
        values
        (%s, %s,
        %f, %f, %f,
        %f, %f, %f)        
        """ %
        (id, t, r, p, y, x_accel, y_accel, z_accel)
        )
    #c.commit()


SETTINGS_FILE = "RTIMULib"

print("Using settings file " + SETTINGS_FILE + ".ini")
if not os.path.exists(SETTINGS_FILE + ".ini"):
  print("Settings file does not exist, will be created")

s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)

print("IMU Name: " + imu.IMUName())

if (not imu.IMUInit()):
    print("IMU Init Failed")
    sys.exit(1)
else:
    print("IMU Init Succeeded")
# this is a good time to set any fusion parameters
imu.setSlerpPower(0.02)
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(True)

poll_interval = imu.IMUGetPollInterval()
print("Poll Interval: %d (ms)\n" % poll_interval)
last_time = time.time()

count = 0;


while True:
    try:

        if imu.IMURead():

            data       = imu.getIMUData()
            fusionPose = data["fusionPose"]      
            accel      = data["accel"]
            
            db_insert(conn,
                      fusionPose[0],
                      fusionPose[1],
                      fusionPose[2],
                      accel[0],
                      accel[1],
                      accel[2])


            count += 1
            refresh_rate = 1.0/ (time.time() - last_time)
            last_time = time.time()
            os.write(0, "\r(%2f. hz) %d" % (refresh_rate,count));
            time.sleep(poll_interval*0.5/1000.0)
    except:
        conn.commit();
        raise;
      
