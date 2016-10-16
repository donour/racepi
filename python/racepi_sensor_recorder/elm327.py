#!/usr/bin/env python2
import serial
import os
import time

BAUD_RATE="115200"
DEV_NAME="/dev/obdlink"

class ElmHandler:

    def __init__(self, dev, baud):

        self.port = serial.Serial(dev, baud)
        if dev != self.port.getPort():
            # port open failed
            raise IOError("Could not open" + dev)

        # TODO : ensure that the device is an elm327 compatible        
        self.send_command('atz'); time.sleep(6) # with for device result
        self.port.read() # empty buffer
                
        self.get_sample('atE0')
        self.elm_version = self.get_sample('ati')
        self.dev_description = self.get_sample('at@1')
        if not 'ELM' in self.elm_version:
            raise IOError("Failed to find ELM device")
        print self.elm_version, self.dev_description

    def get_sample(self, cmd):
        self.send_command(cmd)
        return self.get_result()
        
    def send_command(self, cmd):
        if self.port:
            self.port.flushOutput()
            self.port.flushInput()
            for c in cmd:
                self.port.write(c)
            self.port.write("\r\n")

    def get_result(self):         
        if self.port:
            buffer = ""
            while True:
                c = self.port.read(1)
                if c == '\r' and len(buffer) > 0:
                    break
                else:
                    if buffer != "" or c != ">": #if something is in buffer, add everything
                        buffer = buffer + c

            return buffer
        else:
            return None
                                                                                          
                                                                                     
def record_from_elm327(q, done):

    if not q:
        raise ValueError("Illegal argument, no queue specified")

    elm = ElmHandler(DEV_NAME, BAUD_RATE)

    # TODO : ensure that the device is an elm327 compatible
    # TODO: ensure that al the PIDs requested are available

    while not done.is_set():
        pass

if __name__ == "__main__":
    from multiprocessing import Queue, Event, Process

    done = Event()
    q = Queue()

    p = Process(target=record_from_elm327, args=(q,done))
    p.start()
    while True:
        print q.get()


    

