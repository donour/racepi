#include <stdint.h>
#include <Arduino.h>
#include "BluetoothSerial.h"

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
//    RC_META_BRAKE,
    RC_META_STEERING,
//    RC_META_ENGINE_TEMP,
    RC_META_MAP,
    RC_META_IAT,
    RC_META_MAX
};

const char meta_mesg[] =
    "{"  
        "\"s\":{"  
            "\"meta\": ["  
                "{\"sr\":10,\"nm\":\"Utc\",\"min\":0.0,\"ut\":\"ms\",\"prec\":0,\"max\":0.0},"
                "{\"sr\":10,\"nm\":\"Latitude\",\"min\":0.0,\"ut\":\"Degrees\",\"prec\":6,\"max\":0.0},"
                "{\"sr\":10,\"nm\":\"Longitude\",\"min\":0.0,\"ut\":\"Degrees\",\"prec\":6,\"max\":0.0},"
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
//                "{\"sr\":10,\"nm\":\"Brake\",\"min\":0.0,\"ut\":\"PSI\",\"prec\":1,\"max\":1.0},"
                "{\"sr\":10,\"nm\":\"Steering\",\"min\":-900.0,\"ut\":\"\",\"prec\":1,\"max\":900.0},"
//                "{\"sr\":10,\"nm\":\"EngineTemp\",\"min\":0.0,\"prec\":1,\"max\":0.0},"
                "{\"sr\":10,\"nm\":\"MAP\",\"min\":0.0,\"ut\":\"PSI\",\"prec\":1,\"max\":30.0},"
                "{\"sr\":10,\"nm\":\"IAT\",\"min\":0.0,\"ut\":\"F\",\"prec\":1,\"max\":200.0}"
            "],\"t\":%d" 
        "}" 
    "}\r\n";

int16_t rc_handler_init();
void rc_bt_reader(BluetoothSerial *port, HardwareSerial *debug);

#endif // __RC_PODIUM_
