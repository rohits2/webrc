import RPi.GPIO as GPIO
import numpy as np
from asyncio import sleep, ensure_future
from datetime import datetime

LEFT_PINS = (38,40)
RIGHT_PINS = (3,5)


def sgn(x):
    return 1 if x >= 0 else -1

def power_curve(x, lmbda):
    return sgn(x)*abs(x)**lmbda

class Robot:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LEFT_PINS, GPIO.OUT)
        GPIO.setup(RIGHT_PINS, GPIO.OUT)
        self.left_motor_fwd = GPIO.PWM(*LEFT_PINS)
        self.left_motor_bck = GPIO.PWM(*LEFT_PINS[::-1])
        self.right_motor_fwd = GPIO.PWM(*RIGHT_PINS)
        self.right_motor_bck = GPIO.PWM(*RIGHT_PINS[::-1])
        self.left_motor_fwd.start(0)
        self.left_motor_bck.start(0)
        self.right_motor_fwd.start(0)
        self.right_motor_bck.start(0)
        self.sources = {}
        self.lr = np.array([0., 0.])
        self.inertia = 0.25
        self.last_cmd = 0
        self.drive_task = None

    def drive(self, left, right, cmd_time=datetime.now().timestamp(), source="tele"):
        self.sources[source] = (left, right)
        self.last_cmd = cmd_time
        if self.drive_task is None:
            self.drive_task = self.__update_drive
            ensure_future(self.drive_task())

    def get_info(self):
        return {
            "left": self.left,
            "right": self.right,
            "last_command": self.last_cmd
        }

    async def __update_drive(self):
        while True:
            inputs = np.array(self.sources.values())
            input_lr = inputs.sum(dim=0)

            self.lr = input_lr*(1-self.inertia) + self.lr*self.inertia

            regularizer = abs(self.lr.sum())/2
            lr_reg_matrix = np.eye(2)
            lr_reg_matrix[0,1] = regularizer
            lr_reg_matrix[1,0] = regularizer
            self.lr = (lr_reg_matrix@self.lr)/(1+regularizer)

            left, right = self.lr

            if left >= 0:
                self.left_motor_bck.ChangeDutyCycle(0)
                self.left_motor_fwd.ChangeDutyCycle(int(100*left))
            else:
                self.left_motor_fwd.ChangeDutyCycle(0)
                self.left_motor_bck.ChangeDutyCycle(int(-100*left))

            if right >= 0:
                self.right_motor_bck.ChangeDutyCycle(0)
                self.right_motor_fwd.ChangeDutyCycle(int(100*right))
            else:
                self.right_motor_fwd.ChangeDutyCycle(0)
                self.right_motor_bck.ChangeDutyCycle(int(-100*right))
            await sleep(0.1)
