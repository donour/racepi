#!/usr/bin/env python2
import serial
import time

BAUD_RATE="115200"
DEV_NAME="/dev/obdlink"

class ElmHandler:

    def __init__(self, dev, baud):

        self.port = serial.Serial(dev, baud)
        if dev != self.port.getPort():
            # port open failed
            raise IOError("Could not open" + dev)

        # reset device and wait for startup
        self.__send_command('atz'); time.sleep(6) # with for device result
        self.port.read() # empty buffer

        # disable command echo and line feed
        self.get_sample('atE0')
        self.get_sample('atL0')

        self.elm_version = self.get_sample('ati')
        self.dev_description = self.get_sample('at@1')

        # ensure device is ELM compatible
        if not 'ELM327' in self.elm_version:
            raise IOError("Failed to find ELM device")

        # set automatic protocol selection
        response = self.get_sample('atsp0')
        if 'OK' not in response:
            raise IOError("Failed to set automatic protocol selection")

        # TODO: ensure that al the PIDs requested are available

    def get_is_connected(self):
        """
        Determine if the device is still connected by checking if the ID string
        is the same as during init
        """
        return self.elm_version in self.get_sample('ati')
    
    def get_is_plugged_in(self):
        """
        Determine if the device is plugged into a vehicle by checking the 
        voltage pin reading
        """
        response = self.get_sample('atrv')
        if '0.0V' == response:
            return False
        return True

    def get_sample(self, cmd):
        """
        Send a single ELM AT command and return the one line result
        """
        self.__send_command(cmd)
        return self.__get_result()
        
    def __send_command(self, cmd):
        if self.port:
            self.port.flushOutput()
            self.port.flushInput()
            for c in cmd:
                self.port.write(c)
            self.port.write("\r\n")

    def __get_result(self):         
        if self.port:
            buffer = ""
            while True:
                c = self.port.read(1)
                if c == '\r' and len(buffer) > 0:
                    break
                else:
                    if buffer != "" or c != ">": #if something is in buffer, add everything
                        buffer = buffer + c

            if "no data" in buffer.lower():
                return None                            
            return buffer
        else:
            return None
                                                                                          
                                                                                     
def record_from_elm327(q, done):

    if not q:
        raise ValueError("Illegal argument, no queue specified")

    elm = None
    while not done.is_set():
        while not elm:
            try:
                elm = ElmHandler(DEV_NAME, BAUD_RATE)
                print "ELM device detected: %s (%s)" % (elm.elm_version, elm.dev_description)
                print "ELM connected to vehicle:", str(elm.get_is_plugged_in())
            except serial.SerialException:
                time.sleep(10)
        # TODO : read data from device and publish to queue 
            
if __name__ == "__main__":
    from multiprocessing import Queue, Event, Process

    done = Event()
    q = Queue()

    p = Process(target=record_from_elm327, args=(q,done))
    p.start()
    while True:
        print q.get()


    

