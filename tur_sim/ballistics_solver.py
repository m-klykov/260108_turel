import math
import numpy as np

class BallisticsSolver:
    G = 9.81  # Ускорение свободного падения

    @staticmethod
    def get_lead_point(target_pos, target_velocity, v_muzzle):
        """
        target_pos: текущие мировые координаты [x, y, z]
        target_velocity: вектор скорости [vx, vy, vz]
        v_muzzle: начальная скорость пули
        возвращает точку, куда надо целиться
        """
        dist = np.linalg.norm(target_pos)

        # 1. Приблизительное время полета
        t_fly = dist / v_muzzle

        # 2. Прогноз позиции через t_fly секунд
        lead_pos = target_pos + target_velocity * t_fly

        # Для сверхточных систем можно итеративно уточнить t_fly
        # на основе нового расстояния до lead_pos, но для начала хватит и этого.
        return lead_pos

    @staticmethod
    def calculate_drop(distance, v_muzzle):
        """Возвращает падение снаряда в метрах на заданной дистанции"""
        if v_muzzle <= 0 or distance <= 0:
            return 0.0

        # Время полета: t = S / V
        t_fly = distance / v_muzzle

        # Падение по вертикали: h = (g * t^2) / 2
        drop = (BallisticsSolver.G * (t_fly ** 2)) / 2
        return drop

    @staticmethod
    def get_elevation_adjustment(distance, v_muzzle):
        """Возвращает угол поправки в радианах (на сколько задрать ствол)"""
        drop = BallisticsSolver.calculate_drop(distance, v_muzzle)
        if distance <= 0:
            return 0.0

        # Угол поправки через арктангенс
        return math.atan2(drop, distance)

    @staticmethod
    def estimate_distance(screen_radius, real_radius, focal_length):
        """Дальномер по угловому размеру"""
        if screen_radius <= 0:
            return 0.0
        return (real_radius * focal_length) / screen_radius