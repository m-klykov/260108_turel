import numpy as np
import cv2
import pygame
from .camera_base import CameraBase
from .physical_world import PhysicalWorld


class CameraVirtual(CameraBase):
    def __init__(self, world, width=640, height=480, f=500):
        self.world : PhysicalWorld = world
        self.width = width
        self.height = height
        self.f = f  # Фокусное расстояние в пикселях
        self.cx = width // 2
        self.cy = height // 2

        # Углы поворота пушки/камеры
        self.yaw = 0.0  # горизонталь
        self.pitch = 0.0  # вертикаль

    def _get_rotation_matrix(self):
        # Матрицы для вращения мира ПЕРЕД проекцией
        # Поворачиваем мир в обратную сторону от камеры
        sy, cy = np.sin(-self.yaw), np.cos(-self.yaw)
        R_yaw = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])

        sp, cp = np.sin(-self.pitch), np.cos(-self.pitch)
        R_pitch = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])

        return R_pitch @ R_yaw

    def get_frame(self):
        # Создаем черный кадр
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        R = self._get_rotation_matrix()

        for obj in self.world.objects:
            # 1. Перевод в локальные координаты камеры
            local_pos = R @ obj.pos
            x, y, z = local_pos

            # 2. Отсечение объектов сзади
            if z <= 0.1:
                continue

            # 3. Проекция на плоскость экрана
            screen_x = int(x * self.f / z + self.cx)
            screen_y = int(y * self.f / z + self.cy)

            # Радиус в пикселях зависит от расстояния
            screen_r = int(obj.radius * self.f / z)

            # 4. Рисование (если объект в пределах экрана)
            if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                cv2.circle(frame, (screen_x, screen_y), max(1, screen_r), obj.color, -1)

        return frame