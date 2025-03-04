#include <stdint.h>
#include <Arduino.h>
#include "BluetoothSerial.h"

#ifndef __RC_PODIUM_
#define  __RC_PODIUM_

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
                "{\"sr\":10,\"nm\":\"GSum\",\"min\":-2.0,\"ut\":\"G\",\"prec\":2,\"max\":2.0},"
                "{\"sr\":10,\"nm\":\"Yaw\",\"min\":-300.0,\"ut\":\"Deg/Sec\",\"prec\":1,\"max\":300.0},"
                "{\"sr\":10,\"nm\":\"Pitch\",\"min\":-300.0,\"ut\":\"Deg/Sec\",\"prec\":1,\"max\":300.0},"
                "{\"sr\":10,\"nm\":\"Roll\",\"min\":-300.0,\"ut\":\"Deg/Sec\",\"prec\":1,\"max\":300.0}"
            "],\"t\":%d" 
        "}" 
    "}\r\n";

const char data_mesg[] =
    "{"  
        "\"s\":{"  
            "\"d\": ["  
                "%d,"
                "34.12345,"
                "123.123456,"
                "0.0,"
                "10.0,"
                "14.0,"
                "1.0"
                "0.75,"
                "0.0,"
                "0.0,"
                "0.0,"
                "0.0,"
                "0.0,"
                "0.0,"
                "0.0,"
                "32767"
            "],\"t\":%d" 
        "}" 
    "}\r\n";


int16_t rc_handler_init();
void rc_bt_reader(BluetoothSerial *port, HardwareSerial *debug);

#endif // __RC_PODIUM_
