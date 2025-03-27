from typing import TypedDict
from .webcam_worker import WebcamWorker
import funcnodes_opencv  # noqa: F401 # for typing
import funcnodes as fn
import os
import base64

FUNCNODES_WORKER_CLASSES = [WebcamWorker]
__version__ = "0.1.1"


class BrowserStreamData(TypedDict):
    width: int
    height: int
    channels: int
    data: bytes


@fn.NodeDecorator(
    node_id="webcam.browserwebcam",
    node_name="Browser Webcam",
    default_io_options={
        "delay_ms": {"value_options": {"min": 50}},
        "quality": {"value_options": {"min": 0, "max": 100}},
        "imagedata": {"hidden": True},
    },
    default_render_options={"data": {"src": "out"}},
)
def browser_webcam(
    imagedata: BrowserStreamData,
    delay_ms: int = 1000,  # only used in frontend
    quality: int = 70,  # only used in frontend
    src: str = None,  # only used in frontend
) -> funcnodes_opencv.OpenCVImageFormat:
    """Converts a BrowserStreamData object to an OpenCVImageFormat object."""

    data = imagedata["data"]

    if isinstance(data, str):
        # decode base64 string
        data = base64.b64decode(data)

    return funcnodes_opencv.OpenCVImageFormat.from_bytes(data)


NODE_SHELF = fn.Shelf(
    nodes=[browser_webcam],
    subshelves=[],
    name="Webcam",
    description="Nodes for working with webcams.",
)


REACT_PLUGIN = {
    "module": os.path.join(os.path.dirname(__file__), "react_plugin", "main.js"),
    "css": [],
}
