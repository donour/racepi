#include <Arduino.h>
#include <pthread.h>
#include <string.h>
#include "BluetoothSerial.h"

#include "rc_podium_protocol.h"

static pthread_mutex_t bt_mutex;
#define SERIAL_RX_BUFFER_SIZE (256)

int16_t rc_handler_init() {
  pthread_mutex_init(&bt_mutex, NULL);
  return 0;
}

void rc_bt_reader(BluetoothSerial *port, HardwareSerial *debug) {
    bool enable_data = false;
    char buffer[SERIAL_RX_BUFFER_SIZE];
    unsigned int buffer_index = 0;
    bzero(buffer, SERIAL_RX_BUFFER_SIZE);

    if (NULL == port) {
        return;
    }
    int tick = 0;
    while(1) {
        // overran buffer
        if (buffer_index >= SERIAL_RX_BUFFER_SIZE) {
            buffer_index = 0;
            bzero(buffer, SERIAL_RX_BUFFER_SIZE);
            debug->println("Buffer overrun\n");
        }

        if (port->available()) {
            buffer[buffer_index++] = port->read();

            if (buffer_index >= 2 &&
                buffer[buffer_index - 2] == '\r' &&
                buffer[buffer_index - 1] == '\n') {

                debug->print(buffer);
                if (strstr(buffer, "getMeta")) {
                    debug->println(" >>Meta request");
                    port->printf(meta_mesg, tick++);
                }
                if (strstr(buffer, "setTelemetry")) {
                    if (strstr(buffer, "\"rate\":50")) {
                        enable_data = true;
                        debug->println(" >>Telemetry enabled");
                        port->printf(meta_mesg, tick++);
                    } else {
                        enable_data = false;
                        debug->println(" >>Telemetry disabled");
                    }
                }

                buffer_index = 0;
                bzero(buffer, SERIAL_RX_BUFFER_SIZE);
            }
        } else {
            delay(1);
        }
        if (enable_data) {
            port->printf(data_mesg, millis(), tick++);
            delay(3);
        }

    }

}