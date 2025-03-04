from .webcam_worker import WebcamWorker
import funcnodes_opencv  # noqa: F401 # for typing
import funcnodes as fn

FUNCNODES_WORKER_CLASSES = [WebcamWorker]
__version__ = "0.1.1"


NODE_SHELF = fn.Shelf(
    nodes=[],
    subshelves=[],
    name="Webcam",
    description="Nodes for working with webcams.",
)
