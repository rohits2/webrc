import numpy as np
from datetime import datetime


class Robot:
    def __init__(self):
        self.left: float = 0
        self.right: float = 0
        self.last_cmd: float = 0
        self.inertia = 0.75
        self.i: int = 0

    def drive(self, left, right, cmd_time=datetime.now().timestamp()):
        self.left = self.left * self.inertia + (1 - self.inertia) * left
        self.right = self.right * self.inertia + (1 - self.inertia) * right
        self.last_cmd = cmd_time

    def get_info(self):
        self.i += 1
        return {
            "left": self.left,  #+ 0.1*np.sin(self.i/10),
            "right": self.right,  #+ 0.1*np.cos(self.i/10),
            "last_command": self.last_cmd
        }