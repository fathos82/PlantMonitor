from typing import List

from cams.stream_publisher import StreamPublisher


class CameraManager:
    def __init__(self):
        self.cameras:List[StreamPublisher] = []



    def verify_cam_health(self):
        pass





camera_pool = CameraManager()
