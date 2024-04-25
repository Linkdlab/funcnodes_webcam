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


def convert_to_uint8_img(array: np.ndarray, assert_3_channels: bool = False):
    """converts different types of np.arrays to uint8 by applying apppropriate transformations"""
    # If the array is already uint8, no conversion is needed
    array = array.copy()
    if array.dtype == np.uint8:
        return array

    if assert_3_channels and len(array.shape) == 2:
        array = np.stack([array] * 3, axis=-1)

    floatarray = array.astype(float)
    if array.dtype == bool:
        floatarray *= 255

    minv, maxv = floatarray.min(), floatarray.max()

    if minv >= 0 and maxv <= 255 and (maxv - minv) > 10:
        return floatarray.astype(np.uint8)

    if minv == maxv:
        return np.zeros_like(floatarray, dtype=np.uint8)

    floatarray -= floatarray.min()
    floatarray *= 255 / floatarray.max()
    return floatarray.astype(np.uint8)


def cv2_image_preview_generator(img):
    if isinstance(img, np.ndarray):
        img = convert_to_uint8_img(img)
        # resize the image to a maximum of 800x600 pixels keeping the aspect ratio
        max_width = 800
        max_height = 600
        if img.shape[0] > max_height or img.shape[1] > max_width:
            scale = min(max_width / img.shape[1], max_height / img.shape[0])
            img = cv2.resize(
                img, (int(img.shape[1] * scale), int(img.shape[0] * scale))
            )

        retval, buffer_cv2 = cv2.imencode(
            ".jpeg",
            img,
            [int(cv2.IMWRITE_JPEG_QUALITY), 50],
        )
        return buffer_cv2.tobytes()

    return img
