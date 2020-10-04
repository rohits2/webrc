import cv2
from PIL import Image
from io import BytesIO
import numpy as np
from multiprocessing import Process, Array, Value
from time import sleep as bsleep
from time import time
from asyncio import sleep, get_event_loop
from loguru import logger

TARGET_FPS = 15
TARGET_FRAMETIME = 1 / TARGET_FPS
MAX_W, MAX_H = MAX_RES = 1920, 1080


class VideoCamera(object):
    def __init__(self):
        global MAX_W, MAX_H
        self.video = cv2.VideoCapture(0)
        logger.info("Opened Camera 0!")
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, MAX_W)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, MAX_H)
        _, image = self.video.read()
        H, W, C = image.shape
        MAX_H, MAX_W = H, W
        logger.info("Catching {W}x{H}x{C} frames...".format(W=W, H=H, C=C))
        self.__imbuf = Array("c", H * W * C)
        self.__jpbuf = Array("c", H * W * C * 2)
        self.__jpbufsz = Value("i", 0)
        self.__frameidx = Value("i", 0)
        self.__jpegidx = Value("i", 0)
        self.__quality_adjust = Value("i", 0)
        self.__halt_flag = Value("i", 0)
        self.__H = Value("i", H)
        self.__W = Value("i", W)
        self.__framerate = Value("d", 1)
        self.last_frame = np.frombuffer(self.__imbuf.get_obj(), dtype=np.uint8).reshape(
            H, W, C
        )
        self.last_jpeg = np.frombuffer(self.__jpbuf.get_obj(), dtype=np.uint8).reshape(
            H * W * C * 2, 1
        )

        self.img_proc = Process(target=self.__capture)
        self.img_proc.start()

        self.encode_proc = Process(target=self.__encode)
        self.encode_proc.start()

        self.last_idx = 0
        self.last_frame_timestamp = time()

    def __del__(self):
        self.video.release()
        self.__halt_flag.value = 1
        self.img_proc.join()
        self.encode_proc.join()
        logger.info("Closed Camera 0.")

    def reopen_camera(self):
        return  # TODO: Test this with a camera that isn't bad so that this can actually run
        if self.video is not None:
            self.video.release()
            del self.video
        logger.info(
            "Changing source resolution to {W}x{H}".format(
                W=self.__W.value, H=self.__H.value
            )
        )
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, self.__W.value)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, self.__H.value)
        self.video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G"))

        _, frame = self.video.read()
        H, W, C = frame.shape

        self.__H.value = H
        self.__W.value = W

    def __capture(self):
        while self.__halt_flag.value == 0:
            _, frame = self.video.read()
            H, W, C = frame.shape
            if H / self.__H.value < 0.66666 or H / self.__H.value > 1.5:
                self.reopen_camera()
            self.last_frame[:, :, :] = frame
            self.__frameidx.value += 1

    def __encode(self):
        last_idx = 0
        H, W = MAX_H, MAX_W

        def update_resolution(nH, nW):
            self.__quality_adjust.value = 0
            self.__W.value, self.__H.value = (
                min(max(nW, 120), MAX_W),
                min(max(nH, 160), MAX_H),
            )

        while self.__halt_flag.value == 0:
            while self.__frameidx.value == last_idx:
                continue
            if self.__quality_adjust.value > 5:
                update_resolution(self.__H.value * 8 // 7, self.__W.value * 8 // 7)
            elif self.__quality_adjust.value < -5:
                update_resolution(self.__H.value * 7 // 8, self.__W.value * 7 // 8)

            frame = cv2.resize(self.last_frame, (self.__W.value, self.__H.value), interpolation=cv2.INTER_NEAREST)
            ret, jpeg = cv2.imencode(".jpg", frame)
            bufsz, _ = jpeg.shape
            self.__jpbufsz.value = bufsz
            self.last_jpeg[:bufsz] = jpeg
            last_idx = self.__frameidx.value
            self.__jpegidx.value += 1

    async def get_frame(self):
        while self.last_idx == self.__jpegidx.value:
            await sleep(0)

        self.last_idx = self.__jpegidx.value

        time_now = time()
        elapsed = time_now - self.last_frame_timestamp
        self.last_frame_timestamp = time_now
        self.__framerate.value = (0.8 * self.__framerate.value) + (
            0.2 / elapsed
        )

        if elapsed > 1.2 * TARGET_FRAMETIME:
            self.__quality_adjust.value -= 1
        elif elapsed < 0.8 * TARGET_FRAMETIME:
            self.__quality_adjust.value += 1

        return self.last_jpeg[: self.__jpbufsz.value]

    def get_info(self):
        return {
            "resolution": [self.__W.value, self.__H.value],
            "framerate": self.__framerate.value,
        }
