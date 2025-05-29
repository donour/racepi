#!/usr/bin/env python3
# Copyright 2025 Donour Sizemore
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
from racepi.sensor.handler.stn11xx import STNHandler, DEV_NAME, BAUD_RATE
import time

MODE_22_PIDS = [
    "08", # VVTi B1 intake position
    "4B", # VVTi B2 intake position
    "50", # VVTi B1 exhaust position
    "51", # VVTi B2 exhaust position
    "31", # ign retard from knock (1-4)
    "56", # ign retart from knock (5-6)
    "46", # accel pedal position
    "45", # throttle position
    "6A", # engine torque
    "72", # manifold temp
 ]

OBD_II_MODE01_PIDS = [
    "05", # engine coolant temp
    "0B", # manifold pressure
    "0C", # engine speed
    "43", # abs load
]


def get_obdii_mode01_pid(sh: STNHandler, pid: str) -> str:
    """
    Get the value of a PID in mode 01.
    :param sh: STNHandler object
    :param pid: PID to get
    :return: Value of the PID
    """
    rv = sh.get_pid(mode="01", pid=pid)
    if rv is None:
        return None
    if "STOPPED" in rv:
        rv = sh.get_pid(mode="01", pid=pid)
    # retry read
    if "STOPPED" in rv:
        print(f"PID {pid} read failed twice, returning None")
        return None
    if not pid in rv: return
    assert pid in rv
    #assert rv.startswith(f"0341{pid}"), f"Unexpected response: {rv}"
    vals = rv[4:]
    return vals


def get_obdii_mode22_pid(sh: STNHandler, pid: str) -> str:
    """
    Get the value of a PID in mode 22.
    :param sh: STNHandler object
    :param pid: PID to get
    :return: Value of the PID
    """
    rv = sh.get_pid(mode="22 02", pid=pid)
    if "STOPPED" in rv:
        rv = sh.get_pid(mode="22 02", pid=pid)
    # retry read
    if "STOPPED" in rv:
        print(f"PID {pid} read failed twice, returning None")
        return None
    assert pid in rv
    #assert rv.startswith(f"056202{pid}"), f"Unexpected response: {rv}"
    assert len(rv) >= 6
    vals = rv[6:]
    return vals


def log_vvt(sh: STNHandler) -> None:
    # engine speed
    rv = get_obdii_mode01_pid(sh, "0C")
    engine_speed = int(rv, 16) // 4 
    # MAP
    rv = get_obdii_mode01_pid(sh, "0B")
    pressure = int(rv, 16)
    # cam angles
    rv = get_obdii_mode22_pid(sh, "08")        
    intake_vvti_b1 = parse_int16(rv[0:4]) / 4
    rv = get_obdii_mode22_pid(sh, "50")
    exhaust_vvti_b2 = parse_int16(rv[0:4]) / 4
    # TPS
    rv = get_obdii_mode22_pid(sh, "45")
    tps = int(rv, 16) * 100.0 / 1024.0
    # print a CSV line of all variables
    print(f"{time.time()}, {engine_speed},{pressure},{tps},{intake_vvti_b1},{exhaust_vvti_b2}")

def parse_int16(v: str) -> int:
    """Pack 4 characters from v into a 16-bit signed integer and return it."""
    assert len(v) == 4
    return int.from_bytes(bytes.fromhex(v), byteorder='big', signed=True)

def log_misfires(sh: STNHandler) -> None:
    # engine speed
    rv = get_obdii_mode01_pid(sh, "0C")
    engine_speed = int(rv, 16) // 4
    # load absolute
    rv = get_obdii_mode01_pid(sh, "43")
    load = int(rv, 16) * 100.0 / 255.0
    # MAP
    rv = get_obdii_mode01_pid(sh, "0B")
    pressure = int(rv, 16)
    # knock restard
    rv = get_obdii_mode22_pid(sh, "31")
    knock_ret1 = int(rv[0:1], 16)
    knock_ret2 = int(rv[2:3], 16)
    knock_ret3 = int(rv[4:5], 16)
    knock_ret4 = int(rv[6:7], 16)
    rv = get_obdii_mode22_pid(sh, "56")
    knock_ret5 = int(rv[0:1], 16)
    knock_ret6 = int(rv[2:3], 16)

    # print a CSV line of all variables
    print(f"{time.time()}, {engine_speed},{load}, {pressure},{knock_ret1},{knock_ret2},{knock_ret3},{knock_ret4},{knock_ret5},{knock_ret6}")

if __name__ == "__main__":
    sh = STNHandler("/dev/tty.usbserial-113010774277", baud=115200, headers=False)
    print("STN11xx device initialized")

    while True:
        #log_vvt(sh)
        try:
            log_vvt(sh)
        except TypeError as e:
            pass
        except ValueError as e:
            pass