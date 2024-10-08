from typing import List
import sys
import cv2
import time
import asyncio
from multiprocessing import Process, Queue
import numpy as np

if sys.platform.startswith("win"):

    def VideoCapture(index):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        # disable auto exposure
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        return cap

    def RawVideoCapture(index):
        cap = cv2.VideoCapture(index)

        cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

else:

    def RawVideoCapture(index):
        cap = cv2.VideoCapture(index, cv2.CAP_V4L)
        cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def VideoCapture(index):
        return cv2.VideoCapture(index, cv2.CAP_V4L)


def get_available_cameras(queue, max_index=10) -> List[int]:
    available_devices = []
    for i in range(max_index):
        cap = VideoCapture(i)
        if cap.isOpened():
            available_devices.append(i)
            cap.release()
    queue.put(available_devices)
    return available_devices


AVAILABLE_DEVICES = []
LAST_DEVICE_UPDATE = 0
DEVICE_UPDATE_TIME = 20


async def list_available_cameras(max_index=10):
    """
    List the indices of all available video capture devices.

    Parameters:
    - max_index: Maximum device index to check. Increase if you have more devices.

    Returns:
    - List of integers, where each integer is an index of an available device.
    """
    global AVAILABLE_DEVICES, LAST_DEVICE_UPDATE
    if time.time() - LAST_DEVICE_UPDATE > DEVICE_UPDATE_TIME:
        LAST_DEVICE_UPDATE = time.time()
        print(f"Checking for available devices up to index {max_index}.")

        queue = Queue()
        proc = Process(target=get_available_cameras, args=(queue, max_index))
        proc.start()
        while proc.is_alive():
            await asyncio.sleep(0.1)
        proc.join()
        # check if the process ended with an error
        res = None
        if proc.exitcode != 0:
            return AVAILABLE_DEVICES
        res = queue.get()

        AVAILABLE_DEVICES = res
    return AVAILABLE_DEVICES
