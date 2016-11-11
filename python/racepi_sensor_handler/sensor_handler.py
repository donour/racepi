# Copyright 2016 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

from multiprocessing import Pipe, Event, Process


class SensorHandler:
    """
    Base handler class for using producer-consumer sensor reading, using
    multiproccess
    """
    def __init__(self, read_func):
        self.doneEvent = Event()
        self.pipe_out, self.pipe_in = Pipe()
        self.process = Process(target=read_func)

    def start(self):
        """
        Begin recording data
        :return:
        """
        self.process.start()
        
    def stop(self):
        """
        Stop recording data
        :return:
        """
        self.doneEvent.set()
        self.process.join(3)
        self.process.terminate()

    def get_all_data(self):
        """
        Read all queued data from sensor handler
        :return: list of sensor data tuples, each tuple is (time, value)
        """
        data = []
        while self.pipe_in.poll():
            data.append(self.pipe_in.recv())
        return data

