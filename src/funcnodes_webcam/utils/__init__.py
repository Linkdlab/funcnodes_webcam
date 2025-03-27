from typing import List
import sys
import cv2
import time
import asyncio
from multiprocessing import Process, Queue

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


CAPTURE_BACKENDS = {}


def _add_capture_backend(name: str, attr: str):
    """
    Attempts to add a capture backend to the CAPTURE_BACKENDS dictionary.

    Args:
        name (str): Single-word description of the backend.
        attr (str): The attribute name in cv2 corresponding to the backend.
    """
    try:
        CAPTURE_BACKENDS[name] = getattr(cv2, attr)
    except AttributeError:
        pass  # Backend not available in the current OpenCV build


_add_capture_backend("ANY", "CAP_ANY")  # Auto-detect backend
_add_capture_backend("V4L", "CAP_V4L")  # Video4Linux legacy API
_add_capture_backend("V4L2", "CAP_V4L2")  # Video4Linux2 API
_add_capture_backend("FFMPEG", "CAP_FFMPEG")  # FFMPEG backend
_add_capture_backend("GSTREAMER", "CAP_GSTREAMER")  # GStreamer backend
_add_capture_backend("QT", "CAP_QT")  # QuickTime backend
_add_capture_backend("UNIX_DEVICE", "CAP_UNIX_DEVICE")  # UNIX V4L device
_add_capture_backend("DSHOW", "CAP_DSHOW")  # DirectShow (Windows)
_add_capture_backend("MSMF", "CAP_MSMF")  # Media Foundation (Windows)
_add_capture_backend("AVFOUNDATION", "CAP_AVFOUNDATION")  # AVFoundation (macOS)
_add_capture_backend("INTELPERC", "CAP_INTELPERC")  # Intel Perceptual Computing SDK
_add_capture_backend("OPENNI", "CAP_OPENNI")  # OpenNI (deprecated)
_add_capture_backend("OPENNI2", "CAP_OPENNI2")  # OpenNI2
_add_capture_backend("GIGANETIX", "CAP_GIGANETIX")  # Giganetix API
_add_capture_backend("MIL", "CAP_MIL")  # MIL (Matrox Imaging Library)
_add_capture_backend("ARAVIS", "CAP_ARAVIS")  # Aravis library
_add_capture_backend("XINE", "CAP_XINE")  # Xine backend
_add_capture_backend("XIMGPROC", "CAP_XIMGPROC")  # Extra Image Processing
_add_capture_backend("OPENCV_MJPEG", "CAP_OPENCV_MJPEG")  # OpenCV MJPEG backend
_add_capture_backend("ZED", "CAP_ZED")  # ZED SDK
_add_capture_backend("VFW", "CAP_VFW")  # Video for Windows (deprecated)
_add_capture_backend("CMAKE", "CAP_CMAKE")  # CMake configuration
_add_capture_backend("CLIB", "CAP_CLIB")  # C library backend
_add_capture_backend("DI", "CAP_DI")  # DirectInput
_add_capture_backend("XINE2", "CAP_XINE2")  # Xine2 backend
_add_capture_backend("PXCORE", "CAP_PXCORE")  # PXCORE backend
_add_capture_backend("VIDEOTOOLBOX", "CAP_VIDEOTOOLBOX")  # VideoToolbox (macOS)
_add_capture_backend("MSVIDEO", "CAP_MSVIDEO")  # Microsoft Video
_add_capture_backend("OPENNI2_ASUS", "CAP_OPENNI2_ASUS")  # OpenNI2 ASUS variant
_add_capture_backend("OPENNI_ASUS", "CAP_OPENNI_ASUS")  # OpenNI ASUS variant
_add_capture_backend("KIWI", "CAP_KIWI")  # Kiwi backend
_add_capture_backend("DALSA", "CAP_DALSA")  # DALSA backend
_add_capture_backend("GPHOTO2", "CAP_GPHOTO2")  # gPhoto2 backend (camera control)
_add_capture_backend("POPPER", "CAP_POPPER")  # Popper backend
_add_capture_backend("QTKIT", "CAP_QTKIT")  # QtKit (deprecated)
_add_capture_backend("WMCAP", "CAP_WMCAP")  # Windows Media Capture
_add_capture_backend("WIGI", "CAP_WIGI")  # WIGI backend

if sys.platform.startswith("win"):
    DEFAULT_BACKEND = ("ANY", CAPTURE_BACKENDS["ANY"])
else:
    DEFAULT_BACKEND = ("V4L2", CAPTURE_BACKENDS["V4L2"])
