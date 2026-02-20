/**************************************************************************
    Copyright 2025 Donour Sizemore

    This file is part of RacePi

    RacePi is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2.

    RacePi is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
**************************************************************************/

#include <stdint.h>
#include <Arduino.h>

#ifndef __RC_PODIUM_
#define  __RC_PODIUM_

enum {
    RC_META_UTC = 0,
    RC_META_LATITUDE,
    RC_META_LONGITUDE,
    RC_META_SPEED,
    RC_META_ALTITUDE,
    RC_META_GPSSATS,
    RC_META_GPSQUAL,
    RC_META_GPSDOP,
    RC_META_ACCELX,
    RC_META_ACCELY,
    RC_META_ACCELZ,
    RC_META_YAW,
    RC_META_PITCH,
    RC_META_ROLL,
    RC_META_RPM,
    RC_META_TPS,
    RC_META_BRAKE,
    RC_META_CLUTCH,
    RC_META_STEERING,
    RC_META_SPORT_MODE,
    RC_META_TC_DISABLE,
    RC_META_ENGINE_TEMP,
    RC_META_IAT,
    RC_META_FUEL_LEVEL,
    RC_META_ENGINE_TORQUE,
    RC_META_TC_TORQUE,
    RC_META_WHEEL_SPEED_LF,
    RC_META_WHEEL_SPEED_RF,
    RC_META_WHEEL_SPEED_LR,
    RC_META_WHEEL_SPEED_RR,
    RC_META_MAX
};

const char meta_mesg[] =
    "{"  
        "\"s\":{"  
            "\"meta\": ["  
                "{\"sr\":10,\"nm\":\"Utc\",\"min\":0.0,\"ut\":\"ms\",\"prec\":0,\"max\":0.0},"
                "{\"sr\":10,\"nm\":\"Latitude\",\"min\":0.0,\"ut\":\"Degrees\",\"prec\":8,\"max\":0.0},"
                "{\"sr\":10,\"nm\":\"Longitude\",\"min\":0.0,\"ut\":\"Degrees\",\"prec\":8,\"max\":0.0},"
                "{\"sr\":10,\"nm\":\"Speed\",\"min\":0.0,\"ut\":\"mph\",\"prec\":2,\"max\":150.0},"
                "{\"sr\":10,\"nm\":\"Altitude\",\"min\":0.0,\"ut\":\"ft\",\"prec\":1,\"max\":1000.0},"
                "{\"sr\":10,\"nm\":\"GPSSats\",\"min\":0.0,\"ut\":\"\",\"prec\":1,\"max\":20.0},"
                "{\"sr\":10,\"nm\":\"GPSQual\",\"min\":0.0,\"ut\":\"\",\"prec\":1,\"max\":5.0},"
                "{\"sr\":10,\"nm\":\"GPSDOP\",\"min\":0.0,\"ut\":\"\",\"prec\":1,\"max\":10.0},"
                "{\"sr\":10,\"nm\":\"AccelX\",\"min\":-2.0,\"ut\":\"G\",\"prec\":2,\"max\":2.0},"
                "{\"sr\":10,\"nm\":\"AccelY\",\"min\":-2.0,\"ut\":\"G\",\"prec\":2,\"max\":2.0},"
                "{\"sr\":10,\"nm\":\"AccelZ\",\"min\":-2.0,\"ut\":\"G\",\"prec\":2,\"max\":2.0},"
                "{\"sr\":10,\"nm\":\"Yaw\",\"min\":-300.0,\"ut\":\"Deg/Sec\",\"prec\":1,\"max\":300.0},"
                "{\"sr\":10,\"nm\":\"Pitch\",\"min\":-300.0,\"ut\":\"Deg/Sec\",\"prec\":1,\"max\":300.0},"
                "{\"sr\":10,\"nm\":\"Roll\",\"min\":-300.0,\"ut\":\"Deg/Sec\",\"prec\":1,\"max\":300.0},"
                "{\"sr\":10,\"nm\":\"RPM\",\"min\":0.0,\"ut\":\"\",\"prec\":0,\"max\":10000.0},"
                "{\"sr\":10,\"nm\":\"TPS\",\"min\":0.0,\"ut\":\"%\",\"prec\":0,\"max\":100.0},"
                "{\"sr\":10,\"nm\":\"Brake\",\"min\":0.0,\"ut\":\"\",\"prec\":2,\"max\":1.0},"
                "{\"sr\":10,\"nm\":\"Clutch\",\"min\":0.0,\"ut\":\"\",\"prec\":2,\"max\":3.0},"
                "{\"sr\":10,\"nm\":\"Steering\",\"min\":-900.0,\"ut\":\"\",\"prec\":1,\"max\":900.0},"
                "{\"sr\":10,\"nm\":\"SportMode\",\"min\":0.0,\"ut\":\"\",\"prec\":1,\"max\":1.0},"
                "{\"sr\":10,\"nm\":\"TCDisable\",\"min\":0.0,\"ut\":\"\",\"prec\":1,\"max\":1.0},"
                "{\"sr\":10,\"nm\":\"EngineTemp\",\"min\":0.0,\"ut\":\"F\",\"prec\":1,\"max\":260.0},"
                "{\"sr\":10,\"nm\":\"IAT\",\"min\":0.0,\"ut\":\"F\",\"prec\":1,\"max\":200.0},"
                "{\"sr\":10,\"nm\":\"FuelLevel\",\"min\":0.0,\"ut\":\"liters\",\"prec\":0,\"max\":100.0},"
                "{\"sr\":10,\"nm\":\"EngineTorque\",\"min\":0.0,\"ut\":\"nm\",\"prec\":0,\"max\":500.0},"
                "{\"sr\":10,\"nm\":\"TCTorque\",\"min\":0.0,\"ut\":\"nm\",\"prec\":0,\"max\":911.0},"
                "{\"sr\":10,\"nm\":\"WheelSpdLF\",\"min\":0.0,\"ut\":\"\",\"prec\":0,\"max\":150.0},"
                "{\"sr\":10,\"nm\":\"WheelSpdRF\",\"min\":0.0,\"ut\":\"\",\"prec\":0,\"max\":150.0},"
                "{\"sr\":10,\"nm\":\"WheelSpdLR\",\"min\":0.0,\"ut\":\"\",\"prec\":0,\"max\":150.0},"
                "{\"sr\":10,\"nm\":\"WheelSpdRR\",\"min\":0.0,\"ut\":\"\",\"prec\":0,\"max\":150.0}"
            "],\"t\":%d" 
        "}" 
    "}\r\n";
                //                "{\"sr\":10,\"nm\":\"OilTemp\",\"min\":0.0,\"ut\":\"F\",\"prec\":1,\"max\":280.0},"
                //"{\"sr\":10,\"nm\":\"TorqueLimit\",\"min\":0.0,\"ut\":\"nm\",\"prec\":0,\"max\":911.0},"
//                "{\"sr\":10,\"nm\":\"MAP\",\"min\":0.0,\"ut\":\"PSI\",\"prec\":1,\"max\":30.0},"

int16_t rc_handler_init();
void rc_bt_reader(HardwareSerial *debug, void (*rc_enable_callback)(bool));
void rc_set_data(const int index,const float value);

static uint64_t rc_epoch = 0;


#endif // __RC_PODIUM_
