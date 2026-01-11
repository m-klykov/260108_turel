import math

import numpy as np

from .camera_virtual import CameraVirtual
from .physical_object import PhysicalObject
from .motion_base import MotionLinear, MotionBallistic  # Предположим, пуля летит прямо
from .physical_world import PhysicalWorld

class TurretModel:
    BULLET_RADIUS = 0.2
    def __init__(self, camera, world):
        self.camera : CameraVirtual = camera  # Турель "несет" камеру
        self.world : PhysicalWorld = world
        self.yaw = 0.0
        self.pitch = 0.0

        # Целевое положение (куда хотим смотреть)
        self.target_yaw = 0.0
        self.target_pitch = 0.0

        #поворот по клавишам
        self.turn_speed = math.radians(20)
        #поворот по точке
        self.max_turn_speed = math.radians(60)

        self.projectile_speed = 50.0  # м/с

        # признак, что мы уперлись в предел скорости турели
        self.limited_turn = False

    def set_direct_target_angles(self, yaw, pitch):
        """Прямая устанока угла"""
        self.set_target_angles(yaw, pitch)

        self.yaw = self.target_yaw
        self.pitch = self.target_pitch

    def set_target_angles(self, yaw, pitch):
        """Устанавливаем точку, куда турель должна начать плавно поворачиваться"""
        self.target_yaw = yaw
        # Ограничим наклон, чтобы пушка не делала "сальто" (от -90 до +90 град)
        self.target_pitch = max(math.radians(-89), min(math.radians(89), pitch))

        # print(f"set target angles {self.target_yaw:0.2f} {self.target_pitch:0.2f}")

    def _approach(self, current, target, max_delta):
        """Вспомогательная функция для плавного движения к цели"""
        diff = target - current
        # Если мы очень близко (меньше 0.01 рад), не дергаемся
        if abs(diff) < 0.001:
            return current

        # Плавное замедление: если дистанция меньше шага, уменьшаем шаг
        if abs(diff)<max_delta:
            actual_step = abs(diff) / 2
        else:
            actual_step = max_delta
            self.limited_turn = True

        # actual_step = min(max_delta, abs(diff) * 0.5)
        return current + math.copysign(actual_step, diff)

    def update(self, dt):
        # Максимальный поворот за этот кадр
        step = self.max_turn_speed * dt

        self.limited_turn = False
        # Плавно двигаем углы
        self.yaw = self._approach(self.yaw, self.target_yaw, step)
        self.pitch = self._approach(self.pitch, self.target_pitch, step)

        # Синхронизируем камеру с актуальными углами
        self.camera.yaw = self.yaw
        self.camera.pitch = self.pitch


    def turn(self, dx, dy):
        """воворот в указанное направлении с клавиатуры"""
        new_yaw = self.yaw + dx * self.turn_speed
        new_pitch = self.pitch + dy * self.turn_speed

        self.set_target_angles(new_yaw, new_pitch)

    def fire(self):
        """Создает снаряд, летящий в направлении взгляда турели"""
        # Вычисляем вектор направления на основе Yaw и Pitch
        # В локальных координатах камеры это всегда ось Z
        # Но нам нужно выстрелить в МИРОВЫХ координатах

        dir_x = np.sin(self.yaw) * np.cos(self.pitch)
        dir_y = -np.sin(self.pitch)
        dir_z = np.cos(self.yaw) * np.cos(self.pitch)

        direction = np.array([dir_x, dir_y, dir_z])
        velocity = direction * self.projectile_speed

        # Снаряд: маленький зеленый шарик
        projectile = PhysicalObject(
            pos= [0, 0, 0],  # Вылет из начала координат (где стоит пушка)
            radius= self.BULLET_RADIUS,
            color= (0, 255, 0),
            obj_type= "bullet",
            behavior= MotionBallistic(velocity=velocity),
            lifetime= 3.0  # Пуля исчезнет через 3 секунды сама

        )
        self.world.add_object(projectile)

        return projectile

