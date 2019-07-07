import cv2
from PIL import Image
from io import BytesIO
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
        logger.info("Catching {W}x{H}x{C} frames...".format(W=W, H=H, C=C))
        self.__imbuf = Array('c', H * W * C)
        self.__jpbuf = Array('c', H * W * C * 2)
        self.__jpbufsz = Value('i', 0)
        self.__frameidx = Value('i', 0)
        self.__jpegidx = Value('i', 0)
        self.__halt_flag = Value('i', 0)
        self.last_frame = np.frombuffer(self.__imbuf.get_obj(), dtype=np.uint8).reshape(H, W, C)
        self.last_jpeg = np.frombuffer(self.__jpbuf.get_obj(), dtype=np.uint8).reshape(H * W * C * 2, 1)

        self.img_proc = Process(target=self.__capture)
        self.img_proc.start()

        self.encode_proc = Process(target=self.__encode)
        self.encode_proc.start()

        self.last_idx = 0

    def __del__(self):
        self.video.release()
        self.__halt_flag.value = 1
        self.img_proc.join()
        self.encode_proc.join()
        logger.info("Closed Camera 0.")

    def __capture(self):
        while self.__halt_flag.value == 0:
            _, frame = self.video.read()
            self.last_frame[:, :, :] = frame
            self.__frameidx.value += 1

    """def __encode(self):
        while self.__halt_flag.value == 0:
            jpeg_buf = BytesIO()
            img = Image.fromarray(self.last_frame)
            img.save(jpeg_buf, format="jpeg", quality=80, optimize=True, progressive=True)
            jpeg = np.frombuffer(jpeg_buf.getbuffer(), dtype=np.uint8)
            self.__jpbufsz.value = jpeg.shape[0]
            self.last_jpeg[:jpeg.shape[0]] = jpeg"""

    def __encode(self):
        last_idx = 0
        while self.__halt_flag.value == 0:
            while self.__frameidx.value == last_idx:
                bsleep(1/60)
                #logger.info("Stalled on new frame")
                continue
            ret, jpeg = cv2.imencode('.jpg', self.last_frame)
            bufsz, _ = jpeg.shape
            self.__jpbufsz.value = bufsz
            self.last_jpeg[:bufsz] = jpeg
            last_idx = self.__frameidx.value
            self.__jpegidx.value += 1


    async def get_frame(self):
        while self.last_idx == self.__jpegidx.value:
            logger.info("Stalled on new JPEG")
            await sleep(1/30)
        self.last_idx = self.__jpegidx.value
        return self.last_jpeg[:self.__jpbufsz.value]
