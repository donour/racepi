from multiprocessing import Queue, Event, Process

class SensorHandler:    
    """
    Base handler class for using producer-consumer sensor reading, using
    multiproccess
    """
    def __init__(self, read_func):
        self.doneEvent = Event()
        self.data_q = Queue()
        self.process = Process(target=read_func)

    def start(self):
        self.process.start()

    def stop(self):
        self.doneEvent.set()
        self.process.join()

    def get_all_data(self):
        data = []
        while not self.data_q.empty():
            data.append(self.data_q.get())
        return data

