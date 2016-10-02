import multiprocessing

imu_q = multiprocessing.Queue()
imu_recording_done = multiprocessing.Event()