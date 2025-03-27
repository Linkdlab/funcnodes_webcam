from all_nodes_test_base import TestAllNodesBase
from typing import List
import unittest

from funcnodes_webcam import browser_webcam
import numpy as np
import cv2
import base64
from funcnodes_opencv import OpenCVImageFormat


class TestAllNodes(TestAllNodesBase):
    #  in this test class all nodes should be triggered at least once to mark them as testing
    sub_test_classes: List[unittest.IsolatedAsyncioTestCase] = []

    async def test_browser_webcam(self):
        randomimage = np.random.randint(0, 255, (480, 640, 3), np.uint8)
        random_jpg_byted = cv2.imencode(".jpg", randomimage)[1].tobytes()
        random_base64 = base64.b64encode(random_jpg_byted).decode("utf-8")
        data = {
            "width": 640,
            "height": 480,
            "channels": 3,
            "data": random_base64,
        }
        res = await browser_webcam.inti_call(imagedata=data)
        self.assertIsInstance(res, OpenCVImageFormat)
