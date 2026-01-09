import numpy as np
from tur_sim.ballistics_solver import BallisticsSolver


class MotionBase:
    def get_next_pos(self, current_pos, dt):
        return current_pos

class MotionLinear(MotionBase):
    def __init__(self,velocity):
        self.velocity = velocity

    def get_next_pos(self, current_pos, dt):
        return current_pos + self.velocity * dt


class MotionBallistic:
    def __init__(self, velocity, g = BallisticsSolver.G):
        self.velocity = np.array(velocity, dtype=float)
        self.g = g

    def get_next_pos(self, current_pos, dt):
        # 1. Обновляем скорость (гравитация тянет вниз по оси Y)
        # ВНИМАНИЕ: Если у вас в мире Y растет ВНИЗ, используйте +self.g
        # Если Y растет ВВЕРХ (классика), используйте -self.g
        self.velocity[1] += self.g * dt

        # 2. Вычисляем новое положение
        new_pos = current_pos + self.velocity * dt
        return new_pos

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


class MotionPointToPoint:
    def __init__(self, start_pos, end_pos, speed):
        self.start_pos = np.array(start_pos, dtype=float)
        self.end_pos = np.array(end_pos, dtype=float)
        self.speed = speed

        # Вычисляем направление один раз при инициализации
        direction = self.end_pos - self.start_pos
        self.dist_total = np.linalg.norm(direction)
        self.dir_unit = direction / self.dist_total if self.dist_total > 0 else direction

    def get_next_pos(self, current_pos, dt):
        # Рассчитываем шаг за этот кадр
        step = self.dir_unit * self.speed * dt
        new_pos = current_pos + step

        # Проверяем, не пролетели ли мы конечную точку
        # Считаем текущее расстояние от старта
        dist_from_start = np.linalg.norm(new_pos - self.start_pos)

        if dist_from_start >= self.dist_total:
            # Если достигли или перелетели — сброс на старт
            return self.start_pos.copy()

        return new_pos