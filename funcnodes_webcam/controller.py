from typing import Optional
import threading
import time
import numpy as np
import asyncio
from .utils import list_available_cameras, VideoCapture


class WebcamController:
    def __init__(self) -> None:
        self._device: Optional[int] = None
        self._stop_thread: threading.Event = threading.Event()
        self._capture_thread: Optional[threading.Thread] = None
        self._image_lock = threading.Lock()
        self._last_frame: Optional[np.ndarray] = None
        self.cap_generator = VideoCapture
        self._capturing = False

    async def start_capture(self, device: int = -1):
        """Starts the webcam capture thread."""
        print("Starting capture", device)
        await self.stop_capture()
        if device < 0:
            devicelist = await list_available_cameras()
            if not devicelist:
                devicelist = []
            print(f"Available devices: {devicelist}")
            if len(devicelist) == 0:
                raise ValueError("No available devices.")
            for dev in devicelist:
                try:
                    await self.start_capture(dev)
                except RuntimeError:
                    continue
                return
        if device < 0:
            raise ValueError("No device specified.")
        self._stop_thread.clear()
        self._capturing = True

        cap = self.cap_generator(device)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open device {device}")
        cap.release()
        self._device = device
        self._capture_thread = threading.Thread(target=self._capture_loop)
        self._capture_thread.daemon = True
        self._capture_thread.start()

        print("Capture thread started")

    def _capture_loop(self):
        """Continuously grabs images from the webcam."""
        cap = self.cap_generator(self._device)  # Open the default camera
        try:
            while not self._stop_thread.is_set() and self._capturing:
                if not cap.isOpened():
                    time.sleep(0.1)
                    cap = self.cap_generator(self._device)
                if not cap.isOpened():
                    time.sleep(0.1)
                    continue
                ret, frame = cap.read()

                if ret:
                    # Convert the color space from BGR to RGB
                    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert the frame to PIL image
                    self.last_frame = frame
                time.sleep(0.02)
        finally:
            cap.release()

    @property
    def last_frame(self) -> Optional[np.ndarray]:
        return self.get_last_frame()

    @last_frame.setter
    def last_frame(self, frame):
        self.set_last_frame(frame)

    def set_last_frame(self, frame):
        with self._image_lock:
            self._last_frame = frame

    def get_last_frame(self) -> Optional[np.ndarray]:
        """Returns the last frame captured by the webcam."""
        with self._image_lock:
            return self._last_frame

    async def stop_capture(self):
        """Stops the webcam capture thread."""
        if self._stop_thread is not None or self._capture_thread is not None:
            if self._stop_thread:
                self._stop_thread.set()
            self._capturing = False
            print("Waiting for capture thread to stop")
            while self._capture_thread is not None and self._capture_thread.is_alive():
                await asyncio.sleep(0.05)
            if self._capture_thread is not None:
                self._capture_thread.join()
            await asyncio.sleep(0.1)
            print("Capture thread stopped")
