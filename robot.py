import RPi.GPIO as GPIO
from datetime import datetime

LEFT_PINS = (0, 1)
RIGHT_PINS = (2, 3)


class Robot:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LEFT_PINS, GPIO.OUT)
        GPIO.setup(RIGHT_PINS, GPIO.OUT)
        self.left_motor_fwd: GPIO.PWM = GPIO.PWM(*LEFT_PINS)
        self.left_motor_bck: GPIO.PWM = GPIO.PWM(*LEFT_PINS[::-1])
        self.right_motor_fwd: GPIO.PWM = GPIO.PWM(*RIGHT_PINS)
        self.right_motor_bck: GPIO.PWM = GPIO.PWM(*RIGHT_PINS[::-1])
        self.left: float = 0
        self.right: float = 0
        self.inertia: float = 0.75
        self.last_cmd: float = 0

    def drive(self, left, right, cmd_time=datetime.now().timestamp()):
        self.left = self.left * self.inertia + (1 - self.inertia) * left
        self.right = self.right * self.inertia + (1 - self.inertia) * right
        self.last_cmd = cmd_time

    def get_info(self):
        return {
            "left": self.left,
            "right": self.right,
            "last_command": self.last_cmd
        }

    def __update_drive(self):
        if self.left >= 0:
            self.left_motor_bck.set(0)
            self.left_motor_fwd.set(100*self.left)
        else:
            self.left_motor_fwd.set(0)
            self.left_motor_bck.set(-100*self.left)

        if self.right >= 0:
            self.right_motor_bck.set(0)
            self.right_motor_fwd.set(100*self.right)
        else:
            self.right_motor_fwd.set(0)
            self.right_motor_bck.set(-100*self.right)
