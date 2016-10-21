#!/usr/bin/env python2
import serial
import time

BAUD_RATE="576000"
DEV_NAME="/dev/obdlink"
FORCE_PROTOCOL=6

class STNHandler:

    def __init__(self, dev, baud):

        self.port = serial.Serial(dev, baud)
        if dev != self.port.getPort():
            # port open failed
            raise IOError("Could not open" + dev)

        # reset device and wait for startup
        self.__send_command('atz')
        time.sleep(6) # with for device result
        self.port.read() # empty buffer

        # disable command echo and line feed
        self.__send_command("ATE0")
        self.run_config_cmd("ATL0")
        self.run_config_cmd("ATS0")
        self.run_config_cmd("ATAL")
        self.run_config_cmd("ATH1")

        self.elm_version = self.get_sample('ati')
        self.stn_version = self.get_sample('sti')
        self.dev_description = self.get_sample('at@1')

        # ensure device is ELM compatible
        if not 'ELM327' in self.elm_version:
            raise IOError("Failed to find ELM device")
        # ensure device is STN11xx compatible
        if not 'stn11' in self.stn_version.lower():
            raise IOError("Failed to find STN11xx device: " + self.stn_version )

        # set automatic protocol selection
        self.run_config_cmd("stp 33")
        self.run_config_cmd("atsp " + str(FORCE_PROTOCOL))

        # clear CAN filters and block all messages
        self.run_config_cmd("stfcp")
        self.run_config_cmd("stfcb")
        self.run_config_cmd("stfab FFF,FFF")
        
    def run_config_cmd(self, cmd):
        r = self.get_sample(cmd)
        print cmd, r
        if not 'ok' in r.lower():
            raise IOError("Failed to run cmd: "+cmd)
    
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
            self.port.write("\r")
            time.sleep(0.2) # *sigh* i hate hardware, but i hate python hardware libraries more

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
                                                                                          
                                                                                     
def record_from_stn11xx(q, done):

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
	elm.port.read()
		
	q.put(elm.get_sample("22091a"))
	time.sleep(0.025)

if __name__ == "__main__":

    sh = STNHandler(DEV_NAME, BAUD_RATE)
    
    #send_command("stfap " + sys.argv[1]+",fff")
    #time.sleep(.3)
    #send_command("stm")
    #import os
    #while True:
    #    c= port.read()
	#os.write(1,c)

    

