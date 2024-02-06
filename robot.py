import RPi.GPIO as GPIO
import numpy as np
from datetime import datetime
from collections import namedtuple

from system import daemonize

PWMConfig = namedtuple("PWMConfig", "neg", "pos", "tach")

PWM_FREQUENCY = 50

LEFT_PINS = PWMConfig(7, 8, 25)
RIGHT_PINS = PWMConfig(22, 27, 17)


class Motor:
    def __init__(self, pwm_config: PWMConfig):
        self.pwm_config = pwm_config
        self.pwm = GPIO.PWM(pwm_config.tach, PWM_FREQUENCY)
        self.running = False

    def drive(self, x: float):
        if not self.running:
            self.pwm.start()
            self.running = True
        pos = x > 0
        GPIO.output([self.pwm_config.pos, self.pwm_config.neg], [pos, not pos])
        self.pwm.ChangeDutyCycle(abs(x * 100))


class Robot:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LEFT_PINS, GPIO.OUT)
        GPIO.setup(RIGHT_PINS, GPIO.OUT)
        self.left_motor = Motor(LEFT_PINS)
        self.right_motor = Motor(RIGHT_PINS)

        self.sources = {}
        self.lr = np.array([0.0, 0.0])
        self.inertia = 0.25
        self.last_cmd = 0

    def drive(self, left, right, cmd_time=datetime.now().timestamp(), source="tele"):
        self.sources[source] = (left, right)
        self.last_cmd = cmd_time
        self.__update_drive()

    def get_info(self):
        return {"left": self.lr[0], "right": self.lr[1], "last_command": self.last_cmd}

    
    @daemonize(interval=0.1, critical=True, max_failures=3)
    def __update_drive(self):
        inputs = np.array(list(self.sources.values()))
        input_lr = inputs.sum(axis=0)

        self.lr = input_lr * (1 - self.inertia) + self.lr * self.inertia

        left, right = self.lr
        self.left_motor.drive(left)
        self.right_motor.drive(right)
