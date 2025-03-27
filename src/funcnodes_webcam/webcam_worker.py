from typing import Tuple
from funcnodes import (
    FuncNodesExternalWorker,
    instance_nodefunction,
    NoValue,
)
import time
from .utils import (
    list_available_cameras,
    DEVICE_UPDATE_TIME,
)
from .controller import WebcamController, CAPTURE_BACKENDS, DEFAULT_BACKEND
from funcnodes_opencv import OpenCVImageFormat
from funcnodes_images import ImageFormat
import asyncio


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
        try:
            for node in self.start_capture.nodes(self):
                node.inputs["device"].default_value = NoValue
            self.start_capture.nodeclass(self).input_device.default_value = NoValue
        except KeyError:
            pass

    @instance_nodefunction(
        default_io_options={
            "backend": {
                "value_options": {"options": list(CAPTURE_BACKENDS.keys())},
            }
        }
    )
    async def start_capture(self, device: int = -1, backend: str = DEFAULT_BACKEND[0]):
        device = int(device)
        """Starts the webcam capture thread."""
        await self.controller.set_backend(backend)
        await self.controller.start_capture(device)

    async def update_available_cameras(self):
        available_devices = await list_available_cameras()
        if (
            self.controller._capturing
            and self.controller._device not in available_devices
        ):
            available_devices = [self.controller._device] + available_devices
        available_devices = [-1] + available_devices
        for node in self.start_capture.nodes(self):
            node.inputs["device"].update_value_options(options=available_devices)
        self.start_capture.nodeclass(self).input_device.update_value_options(
            options=available_devices
        )

    @instance_nodefunction()
    async def set_delay(self, delay: float):
        delay = max(0.05, delay)
        self._delay = delay

    @instance_nodefunction(
        outputs=[
            {"name": "actual_width", "type": "int"},
            {"name": "actual_height", "type": "int"},
        ]
    )
    async def set_resolution(self, width: int, height: int) -> Tuple[int, int]:
        print("Setting resolution", width, height)
        res = await self.controller.set_resolution(width, height)
        print("Actual resolution", res)
        return res

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
            asyncio.create_task(self.update_available_cameras())

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
        default_io_options={
            "backend": {
                "value_options": {"options": list(CAPTURE_BACKENDS.keys())},
            }
        }
    )
    async def set_backend(self, backend: str = DEFAULT_BACKEND[0]):
        """Sets the backend of the webcam."""
        return self.controller.set_backend(backend)

    @get_image.triggers
    async def update_image(self):
        """Generates an random image."""
        ...

    async def stop(self):
        await self.stop_capture()
        return await super().stop()
