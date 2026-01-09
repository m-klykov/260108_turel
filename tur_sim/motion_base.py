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


class MotionSpline:
    def __init__(self, min_bounds, max_bounds, num_points, speed):
        self.min_bounds = np.array(min_bounds)
        self.max_bounds = np.array(max_bounds)
        self.num_points = num_points
        self.speed = speed

        # 1. Генерируем случайные ключевые точки (Waypoints)
        self.waypoints = self._generate_waypoints()

        self.current_segment = 0
        self.segment_t = 0.0  # Параметр от 0 до 1 внутри сегмента

    def _generate_waypoints_v01(self):
        # Генерируем точки и замыкаем цикл (добавляем начало в конец)
        points = np.random.uniform(self.min_bounds, self.max_bounds, (self.num_points, 3))
        return np.vstack([points, points[0], points[1], points[2]])  # Для гладкости сплайна

    def _generate_waypoints(self):
        points = []
        min_dist_between = 5.0  # Минимальное расстояние между точками в метрах

        # Первая точка
        points.append(np.random.uniform(self.min_bounds, self.max_bounds))

        while len(points) < self.num_points:
            candidate = np.random.uniform(self.min_bounds, self.max_bounds)

            # Проверяем расстояние до последней добавленной точки
            dist = np.linalg.norm(candidate - points[-1])

            if dist >= min_dist_between:
                points.append(candidate)

        points = np.array(points)
        # Замыкаем сплайн для бесконечного плавного цикла
        return points
        # return np.vstack([points, points[0], points[1], points[2]])

    def _catmull_rom(self, p0, p1, p2, p3, t):
        """Математика сплайна Катмулла-Рома"""
        return 0.5 * (
                (2 * p1) +
                (-p0 + p2) * t +
                (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 +
                (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3
        )

    def get_next_pos(self, current_pos, dt):
        # 1. Получаем 4 индекса точек. Благодаря % num_points они всегда в рамках массива
        idx1 = self.current_segment
        idx0 = (idx1 - 1) % self.num_points
        idx2 = (idx1 + 1) % self.num_points
        idx3 = (idx1 + 2) % self.num_points

        p0 = self.waypoints[idx0]
        p1 = self.waypoints[idx1]
        p2 = self.waypoints[idx2]
        p3 = self.waypoints[idx3]

        # 2. Рассчитываем длину текущего сегмента (между p1 и p2) для постоянной скорости
        segment_len = np.linalg.norm(p2 - p1)

        # Защита от деления на ноль, если точки совпали
        if segment_len > 0.001:
            self.segment_t += (self.speed * dt) / segment_len
        else:
            self.segment_t = 1.0  # Мгновенно переходим дальше

        # 3. Плавный переход к следующему сегменту
        if self.segment_t >= 1.0:
            # Важно: не обнуляем в 0, а вычитаем 1, чтобы сохранить остаток движения
            self.segment_t -= 1.0
            self.current_segment = (self.current_segment + 1) % self.num_points

        # 4. Интерполяция
        return self._catmull_rom(p0, p1, p2, p3, self.segment_t)