#!/usr/bin/env python2
from sense_hat import SenseHat
import atexit

#red = (255, 0, 0)
#sense.show_message("One small step for Pi!", text_colour=red)

IMU_COL=0
GPS_COL=1
OBD_COL=2

class RacePiStatusDisplay:
    """
    Helper class for displaying status information on the PiSenseHat LED matrix
    """

    def __init__(self, senseHat):
        """
        Initialize display with SenseHat instance
        
        This clear the display and sets each sensor
        source to disconnected.

        """
        self.sense = senseHat
        self.__clear()
        self.sense.set_rotation(90)
        atexit.register(self.__clear)

        self.set_col_lost(IMU_COL)
        self.set_col_lost(GPS_COL)
        self.set_col_lost(OBD_COL)
        
    def __clear(self):
        self.sense.clear()

    def __clear_column(self, colNumber):
        for i in range(8):
            self.sense.set_pixel(i,colNumber, 0, 0, 0)

    def set_col_lost(self, colNumber):
        """
        Set specified column to lost/disconnected

        colNumber should be one of the globally specified 
        column numbers.
        """
        self.__clear_column(colNumber)
        self.sense.set_pixel(0, colNumber, 255, 0, 0)

    def set_col_init(self, colNumber):
        """
        Set specified column to initializing/setup

        colNumber should be one of the globally specified 
        column numbers.
        """
        self.__clear_column(colNumber)
        self.sense.set_pixel(0, colNumber, 208, 210, 0)
        self.sense.set_pixel(1, colNumber, 208, 210, 0)

    def set_col_ready(self, colNumber):
        """
        Set specified column to ready/connected

        colNumber should be one of the globally specified 
        column numbers.
        """
        self.__clear_column(colNumber)
        self.sense.set_pixel(0, colNumber, 0, 255, 0)
        self.sense.set_pixel(1, colNumber, 0, 255, 0)
        self.sense.set_pixel(2, colNumber, 0, 255, 0)

    

if __name__ == "__main__":

    s = RacePiStatusDisplay(SenseHat())
    s.set_col_lost(IMU_COL)
    s.set_col_init(GPS_COL)
    s.set_col_ready(OBD_COL)
    
    import time
    while True:
            time.sleep(1)    
