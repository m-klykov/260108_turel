import math

import numpy as np

from .camera_virtual import CameraVirtual
from .physical_object import PhysicalObject
from .motion_base import MotionLinear  # Предположим, пуля летит прямо
from .physical_world import PhysicalWorld



class TurretModel:
    def __init__(self, camera, world):
        self.camera : CameraVirtual = camera  # Турель "несет" камеру
        self.world : PhysicalWorld = world
        self.yaw = 0.0
        self.pitch = 0.0
        self.turn_speed = math.radians(20)
        self.projectile_speed = 50.0  # м/с

    def update(self, dt):
        # Синхронизируем камеру с углами турели
        self.camera.yaw = self.yaw
        self.camera.pitch = self.pitch

    def set_target_angles(self, yaw, pitch):
        """Метод для управления турелью (ручного или автоматического)"""
        self.yaw = yaw
        self.pitch = pitch

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
            radius= 0.1,
            color= (0, 255, 0),
            behavior= MotionLinear(velocity=velocity),
            lifetime= 3.0  # Пуля исчезнет через 3 секунды сама

        )
        self.world.add_object(projectile)

    def turn(self, dx, dy):

        new_yaw = self.yaw + dx * self.turn_speed
        new_pitch = self.pitch + dy * self.turn_speed

        self.set_target_angles(new_yaw, new_pitch)