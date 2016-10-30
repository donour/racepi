#!/usr/bin/env python2
import racepi_sensor_recorder
SQLITE_FILE = '/external/racepi_data/test.db'

sl = racepi_sensor_recorder.SensorLogger(SQLITE_FILE)
sl.start()
