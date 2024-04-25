from typing import Optional
from funcnodes import FuncNodesExternalWorker, instance_nodefunction
from funcnodes.io import NoValue, NodeOutputOptions
import numpy as np
from PIL import Image
import cv2
import threading
import time
import signal
import sys
from .utils import (
    list_available_cameras,
    VideoCapture,
    DEVICE_UPDATE_TIME,
    cv2_image_preview_generator,
)
from .controller import WebcamController
from funcnodes_opencv import OpenCVImageFormat
from funcnodes_images import ImageFormat

DEVICE_UPDATE_TIME = 15


class WebcamWorker(FuncNodesExternalWorker):
    NODECLASSID = "webcam"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = WebcamController()
        self._image: OpenCVImageFormat = None
        self._last_device_update = 0

    @instance_nodefunction()
    async def stop_capture(self):
        await self.controller.stop_capture()
        for node in self.start_capture.nodes(self):
            node.inputs["device"].default_value = NoValue
        self.start_capture.nodeclass(self).input_device.default_value = NoValue

    @instance_nodefunction()
    async def start_capture(self, device: int = -1):
        """Starts the webcam capture thread."""
        await self.controller.start_capture(device)

    async def update_available_cameras(self):
        available_devices = await list_available_cameras()
        if (
            self.controller._capturing
            and self.controller._device not in available_devices
        ):
            available_devices = [self.controller._device] + available_devices
        for node in self.start_capture.nodes(self):
            node.inputs["device"].update_value_options(options=available_devices)
        self.start_capture.nodeclass(self).input_device.update_value_options(
            options=available_devices
        )

    @instance_nodefunction()
    async def set_delay(self, delay: float):
        delay = max(0.05, delay)
        self._delay = delay

    async def loop(self):
        if (
            self.controller._capture_thread is not None
            and self.controller._capture_thread.is_alive()
            and self.controller._capturing
        ):
            await self.update_image()
        #        else:
        if time.time() - self._last_device_update > DEVICE_UPDATE_TIME:
            self._last_device_update = time.time()
            await self.update_available_cameras()

    @instance_nodefunction(
        default_render_options={"data": {"src": "out", "type": "image"}},
    )
    def get_image(self) -> ImageFormat:
        """gets the generated image."""
        self._image = OpenCVImageFormat(self.controller.last_frame)
        if self._image is None:
            return NoValue
        return self._image

    @instance_nodefunction(
        default_render_options={
            "data": {
                "src": "out",
                "type": "plot",
                "plottype": "imshow",
                "colorscale": "bgr",
                "preview_type": "image",
            }
        },
        default_io_options={
            "out": NodeOutputOptions(
                valuepreview_generator=cv2_image_preview_generator,
                valuepreview_type="image",
            )
        },
    )
    def get_image_data(self) -> np.ndarray:
        """gets the generated image."""
        img = self.controller.last_frame
        if img is None:
            return NoValue
        return img

    @get_image.triggers
    async def update_image(self):
        """Generates an random image."""
        ...

    async def stop(self):
        await self.stop_capture()
        return await super().stop()
