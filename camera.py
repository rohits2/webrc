import cv2
import numpy as np
from multiprocessing import Process, Array, Value
from time import sleep as bsleep
from asyncio import sleep, get_event_loop
from loguru import logger


class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        logger.info("Opened Camera 0!")
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        _, image = self.video.read()
        H, W, C = image.shape
        logger.info("Streaming {W}x{H}x{C} frames...".format(W=W, H=H, C=C))
        self.__imbuf = Array('c', H * W * C)
        self.__jpbuf = Array('c', H * W * C)
        self.__jpbufsz = Value('i', 0)
        self.__halt_flag = Value('i', 0)
        self.last_frame = np.frombuffer(self.__imbuf.get_obj(), dtype=np.uint8).reshape(H, W, C)
        self.last_jpeg = np.frombuffer(self.__jpbuf.get_obj(), dtype=np.uint8).reshape(H * W * C, 1)

        self.img_proc = Process(target=self.__capture)
        self.img_proc.start()

    def __del__(self):
        self.video.release()
        self.__halt_flag.value = 1
        self.img_proc.join()
        logger.info("Closed Camera 0.")

    def __capture(self):
        orb = cv2.ORB_create()
        i = 0
        while self.__halt_flag.value == 0:
            success, frame = self.video.read()
            H, W, C = frame.shape
            #if i % 100 == 0:
            #    lf = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            #    kp =  orb.detect(lf, None)
            #cv2.drawKeypoints(frame, kp, frame)
            self.last_frame[:, :, :] = frame  #cv2.resize(frame, (W, H))
            #encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
            ret, jpeg = cv2.imencode('.jpg', self.last_frame)  #, encode_param)
            bufsz, _ = jpeg.shape
            self.__jpbufsz.value = bufsz
            self.last_jpeg[:bufsz] = jpeg

    async def get_frame(self):
        await sleep(0.001)
        return self.last_jpeg[:self.__jpbufsz.value]
