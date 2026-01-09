import math

import numpy as np
import time

from tur_sim.camera_virtual import CameraVirtual


class TrackedTarget:
    def __init__(self, target_id, screen_x, screen_y, raw_dist, camera):
        self.id = target_id
        self.position = camera.get_world_pos_from_screen(screen_x, screen_y, raw_dist)
        self.velocity = np.zeros(3)

        self.last_update_time = time.time()

        # Для фильтрации скорости (чтобы прицел не дергался)
        self.alpha = 0.2  # Коэффициент сглаживания (EMA)

        # Коэффициенты сглаживания (0.05 - 0.2)
        # Чем МЕНЬШЕ число, тем плавнее движение, но больше задержка
        self.pos_alpha = 0.5  # Сглаживание позиции
        self.vel_alpha = 0.5  # Сглаживание скорости (самый шумный параметр)

        self.filtered_dist = raw_dist
        self.dist_alpha = 0.1  # Жесткий фильтр для дистанции (0.05 - 0.15)

    def update_with_screen_data(self, screen_x, screen_y, raw_dist, camera):
        """
        Обновление через сырые данные с камеры.
        Сначала фильтруем дистанцию, потом считаем всё остальное.
        """
        # 1. Фильтруем дистанцию (убираем скачки в пикселях)
        self.filtered_dist = self.filtered_dist * (1 - self.dist_alpha) + raw_dist * self.dist_alpha

        # 2. Получаем мировую позицию, используя УЖЕ ОТФИЛЬТРОВАННУЮ дистанцию
        stable_world_pos = camera.get_world_pos_from_screen(screen_x, screen_y, self.filtered_dist)

        # 3. Вызываем обычный метод обновления позиции и скорости
        self.update(stable_world_pos)

    def update(self, current_world_pos):
        now = time.time()
        dt = now - self.last_update_time

        if dt <= 0.001: return

        new_pos = np.array(current_world_pos, dtype=float)

        # 1. Фильтруем позицию (убирает дрожание самой рамки)
        self.position = self.position * (1 - self.pos_alpha) + new_pos * self.pos_alpha

        # 2. Вычисляем скорость по отфильтрованной позиции
        instant_velocity = (new_pos - self.position) / dt

        # 3. Фильтруем скорость (убирает дерганье прицела "на опережение")
        self.velocity = self.velocity * (1 - self.vel_alpha) + instant_velocity * self.vel_alpha

        self.last_update_time = now

    def predict_position(self, t_ahead):
        """Экстраполяция: где будет цель через t_ahead секунд"""
        return self.position + self.velocity * t_ahead

    def get_fire_solution(self, shooter_pos, projectile_speed, g):
        """
        Главный метод: рассчитывает точку прицеливания с учетом
        упреждения и гравитации.
        """
        dist = np.linalg.norm(self.position - shooter_pos)
        t_fly = dist / projectile_speed

        # Точка упреждения (по вектору скорости)
        lead_point = self.predict_position(t_fly)

        # Баллистическая поправка (превышение над lead_point)
        # h = (g * t^2) / 2
        drop_correction = (g * (t_fly ** 2)) / 2

        # Финальная точка прицеливания (поднимаем по оси Y)
        # ВНИМАНИЕ: Если Y в мире растет вниз, здесь должен быть +
        aim_point = lead_point.copy()
        aim_point[1] -= drop_correction

        return aim_point

    def get_fire_angles(self, shooter_pos, projectile_speed, g):
        """погучение углов для турелт"""
        aim_point = self.get_fire_solution(
            shooter_pos, projectile_speed, g
        )

        # Переводим мировую точку прицеливания в углы для турели
        # (Используем atan2 для Yaw и Pitch)
        target_yaw = math.atan2(aim_point[0], aim_point[2])
        target_pitch = -math.atan2(aim_point[1], np.hypot(aim_point[0], aim_point[2]))

        return target_yaw, target_pitch