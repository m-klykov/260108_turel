import numpy as np

class MotionBase:
    def get_next_pos(self, current_pos, dt):
        return current_pos

class MotionLinear(MotionBase):
    def __init__(self,velocity):
        self.velocity = velocity

    def get_next_pos(self, current_pos, dt):
        return current_pos + self.velocity * dt

class MotionCircular(MotionBase):
    def __init__(self, center, radius, speed):
        self.center = np.array(center)
        self.radius = radius
        self.speed = speed
        self.angle = 0

    def get_next_pos(self, current_pos, dt):
        self.angle += self.speed * dt
        new_x = self.center[0] + np.cos(self.angle) * self.radius
        new_z = self.center[2] + np.sin(self.angle) * self.radius
        return np.array([new_x, current_pos[1], new_z])