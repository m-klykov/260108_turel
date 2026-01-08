import numpy as np
from .motion_base import MotionBase


class PhysicalObject:
    def __init__(self, pos, radius, color, behavior=None):
        self.pos = np.array(pos, dtype=float)      # [x, y, z]
        self.radius = radius # реальный радиус в метрах
        self.color = color   # BGR для OpenCV
        self.behavior : MotionBase = behavior

    def update(self, dt):
        if self.behavior is not None:
            self.pos = self.behavior.get_next_pos(self.pos, dt)