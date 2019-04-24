import cv2
from concurrent.futures import ThreadPoolExecutor
from time import sleep as bsleep
from asyncio import sleep, get_event_loop
from loguru import logger

class VideoCamera(object):
    def __init__(self, frame_rate=24):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0)
        logger.info("Opened Camera 0!")
        self.last_frame = None
        self.frame_rate = frame_rate
        self.buf_exec = ThreadPoolExecutor(1)

    def __del__(self):
        self.video.release()
        logger.info("Closed Camera 0.")


    def __capture(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        self.last_frame = jpeg

    async def get_frame(self):
        loop = get_event_loop()
        await loop.run_in_executor(self.buf_exec, self.__capture)
        return self.last_frame