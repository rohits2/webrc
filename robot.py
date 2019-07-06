import RPi.GPIO as GPIO
from asyncio import sleep, ensure_future
from datetime import datetime

LEFT_PINS = (38,40)
RIGHT_PINS = (3,5)


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
        self.left = 0
        self.right = 0
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
            lefts, rights = zip(*self.sources.values())
            left, right = sum(lefts), sum(rights)
            left, right = max(-1, min(left, 1)), max(-1, min(right, 1))

            self.left = left*(1-self.inertia) + self.left*self.inertia
            self.right = right*(1-self.inertia) + self.right*self.inertia

            left, right = self.left, self.right
            if left*right >= 0:
                delta = left-right
                left -= delta/2
                right += delta/2

            if self.left >= 0:
                self.left_motor_bck.ChangeDutyCycle(0)
                self.left_motor_fwd.ChangeDutyCycle(int(100*left))
            else:
                self.left_motor_fwd.ChangeDutyCycle(0)
                self.left_motor_bck.ChangeDutyCycle(int(-100*left))

            if self.right >= 0:
                self.right_motor_bck.ChangeDutyCycle(0)
                self.right_motor_fwd.ChangeDutyCycle(int(100*right))
            else:
                self.right_motor_fwd.ChangeDutyCycle(0)
                self.right_motor_bck.ChangeDutyCycle(int(-100*right))
            await sleep(0.1)
