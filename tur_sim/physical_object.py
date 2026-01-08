import numpy as np
from .motion_base import MotionBase


class PhysicalObject:
    def __init__(self, pos, radius, color, obj_type="generic", behavior=None, lifetime=None):
        self.pos = np.array(pos, dtype=float)      # [x, y, z]
        self.radius = radius # реальный радиус в метрах
        self.color = color   # BGR для OpenCV
        self.obj_type = obj_type  # "target", "bullet", "debris"
        self.behavior : MotionBase = behavior
        self.lifetime = lifetime  # Время жизни в секундах
        self.is_dead = False  # Флаг для удаления

    def update(self, dt):
        if self.behavior is not None:
            self.pos = self.behavior.get_next_pos(self.pos, dt)

        # Если задано время жизни, уменьшаем его
        if self.lifetime is not None:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.is_dead = True

            # Удаляем, если упало за землю (Y > 0, так как Y вниз обычно в графике,
            # но в физике мы договорились, что земля ниже нуля.
            # Если у вас небо - синее (вверху), значит земля по Y отрицательная или положительная.
            # Допустим, Y=0 - это уровень земли:
            if self.pos[1] > 0:  # Если пуля "ушла" глубоко под землю
                self.is_dead = True