import cv2
import numpy as np 
from multiprocessing import Process, Array, Value
from time import sleep as bsleep
from asyncio import sleep, get_event_loop
from loguru import logger

from matplotlib import pyplot as plt

class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0)
        logger.info("Opened Camera 0!")
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        _, image = self.video.read()
        H, W, C = image.shape
        logger.info("Streaming {W}x{H}x{C} frames...".format(W=W, H=H, C=C))
        self.__imbuf = Array('i', H*W*C//4)
        self.__halt_flag = Value('i', 0)
        self.last_frame = np.frombuffer(self.__imbuf.get_obj(), dtype=np.uint8).reshape(H,W,C)
        
        self.last_blob = None
        self.img_proc = Process(target=self.__capture)
        self.img_proc.start()

    def __del__(self):
        self.video.release()
        self.__halt_flag.value = 1
        self.img_proc.join()
        logger.info("Closed Camera 0.")

    def __capture(self):
        orb = cv2.ORB_create()
        while self.__halt_flag.value == 0:
            success, _ = self.video.read(self.last_frame)
            lf = cv2.cvtColor(self.last_frame, cv2.COLOR_RGB2GRAY)
            kp =  orb.detect(lf, None)
            cv2.drawKeypoints(self.last_frame, kp, self.last_frame)
            

    async def get_frame(self):
        await sleep(0.001)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 45]
        ret, jpeg = cv2.imencode('.jpg', self.last_frame) #, encode_param)
        return jpeg

