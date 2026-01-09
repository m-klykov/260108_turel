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

        self._last_frame = None

    def refresh(self):
        """очистить кеш изображения"""
        self._last_frame = None

    def _get_rotation_matrix(self):
        # Матрицы для вращения мира ПЕРЕД проекцией
        # Поворачиваем мир в обратную сторону от камеры
        sy, cy = np.sin(-self.yaw), np.cos(-self.yaw)
        R_yaw = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])

        sp, cp = np.sin(-self.pitch), np.cos(-self.pitch)
        R_pitch = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])

        return R_pitch @ R_yaw

    def project_point(self, local_pos, real_radius=0):
        """
        Принимает точку в ЛОКАЛЬНЫХ координатах камеры.
        Возвращает (screen_x, screen_y), screen_radius или None, если точка сзади.
        """
        x, y, z = local_pos

        if z <= 0.1:
            return None

        screen_x = int(x * self.f / z + self.cx)
        screen_y = int(y * self.f / z + self.cy)
        screen_r = int(real_radius * self.f / z)

        return (screen_x, screen_y), screen_r

    def get_frame(self):

        if self._last_frame is not None:
            # кеш
            return self._last_frame

        # 1. Создаем пустой кадр
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # 2. Вычисляем положение линии горизонта в пикселях
        # tan(pitch) дает смещение, умножаем на f (фокусное расстояние)
        # Используем минус, так как в OpenCV ось Y направлена вниз
        horizon_y = int(self.cy + np.tan(self.pitch) * self.f)

        # 3. Рисуем Небо и Землю
        # Ограничиваем горизонт пределами кадра, чтобы cv2.rectangle не выдал ошибку
        h_clamped = max(0, min(self.height, horizon_y))

        # Небо (синее) - от 0 до горизонта
        if h_clamped > 0:
            cv2.rectangle(frame, (0, 0), (self.width, h_clamped), (255, 150, 100), -1)  # BGR

        # Земля (зеленая) - от горизонта до низа кадра
        if h_clamped < self.height:
            cv2.rectangle(frame, (0, h_clamped), (self.width, self.height), (100, 100, 100), -1)

        # 5. Рисуем линию направления (Компас / Yaw indicator)
        # Вычисляем смещение по X: если yaw=0, линия в центре.
        # Используем f (фокусное расстояние) для перевода угла в пиксели.
        # Важно: используем sin/cos или просто тангенс угла для проекции.

        # Чтобы линия не пропадала сразу, используем проверку видимости (угол в пределах ~90 град)
        relative_yaw = -self.yaw  # инверсия, так как мир крутится против камеры

        # Условие видимости: если косинус угла положителен, значит направление "перед нами"
        if np.cos(relative_yaw) > 0:
            # Смещение от центра экрана в пикселях
            yaw_x_offset = np.tan(relative_yaw) * self.f
            north_x = int(self.cx + yaw_x_offset)

            # Рисуем линию от низа экрана до горизонта
            if 0 <= north_x <= self.width:
                cv2.line(frame, (self.cx, self.height), (north_x, h_clamped), (150, 150, 150), 2)

        R = self._get_rotation_matrix()

        # 1. Сначала подготавливаем список всех видимых объектов с их глубиной
        render_list = []
        for obj in self.world.objects:
            local_pos = R @ obj.pos
            z = local_pos[2]

            # Если объект перед камерой, добавляем в список на отрисовку
            if z > 0.1:
                render_list.append((z, obj, local_pos))

        # 2. Сортируем список по Z в ОБРАТНОМ ПОРЯДКЕ (от дальних к ближним)
        # z — это расстояние от камеры, чем оно больше, тем объект дальше
        render_list.sort(key=lambda x: x[0], reverse=True)

        # 3. Рисуем объекты из отсортированного списка
        for z, obj, local_pos in render_list:

            # --- РИСУЕМ ТЕНЬ ---
            # Тень всегда на Y=1 (как в вашем коде)
            shadow_pos_world = np.array([obj.pos[0], 1, obj.pos[2]])
            shadow_res = self.project_point(R @ shadow_pos_world, obj.radius)

            if shadow_res:
                (sh_x, sh_y), sh_r = shadow_res
                if 0 <= sh_x < self.width and 0 <= sh_y < self.height:
                    # Тень рисуем чуть прозрачнее или темнее
                    cv2.ellipse(frame, (sh_x, sh_y), (sh_r, sh_r // 2), 0, 0, 360, (60, 60, 60), -1)

            # --- РИСУЕМ ОБЪЕКТ ---
            # Используем уже вычисленный local_pos, чтобы не умножать матрицы дважды
            obj_res = self.project_point(local_pos, obj.radius)

            if obj_res:
                (ox, oy), or_px = obj_res
                if 0 <= ox < self.width and 0 <= oy < self.height:
                    # Основное тело объекта
                    cv2.circle(frame, (ox, oy), max(1, or_px), obj.color, -1)
                    # Контур
                    cv2.circle(frame, (ox, oy), max(1, or_px), (0, 0, 0), 1)

        return frame

    def get_detections(self):
        """Имитация работы нейросети: возвращает список найденных объектов"""
        detections = []
        R = self._get_rotation_matrix()

        for obj in self.world.objects:
            # Проекция (как в get_frame)
            local_pos = R @ obj.pos
            x, y, z = local_pos
            if z <= 0.1: continue

            screen_x = int(x * self.f / z + self.cx)
            screen_y = int(y * self.f / z + self.cy)

            # Проверка, что объект в поле зрения
            if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                detections.append({
                    "type": obj.obj_type,
                    "pos": (screen_x, screen_y),
                    "dist": z  # Дистанция очень важна для баллистики!
                })
        return detections

    # В класс CameraVirtual добавьте метод:
    def get_angles_from_pixel(self, x, y):
        """
        Рассчитывает yaw и pitch, необходимые, чтобы направить центр камеры на точку (x, y).
        x, y - координаты относительно левого верхнего угла кадра (0..width, 0..height).
        """
        # 1. Отклонение от центра в пикселях
        dx = x - self.cx
        dy = y - self.cy

        # 2. Переводим пиксели в углы (приблизительно для малых углов или через arctan)
        # Используем f (фокусное расстояние), чтобы сохранить геометрию
        delta_yaw = np.arctan2(dx, self.f)
        delta_pitch = np.arctan2(dy, self.f)

        # 3. Новые углы = текущие углы + дельта
        return self.yaw + delta_yaw, self.pitch - delta_pitch

    def get_world_pos_from_screen(self, screen_x, screen_y, distance):
        """
        Превращает экранные координаты и дистанцию в мировые координаты [X, Y, Z].
        """
        # 1. Считаем локальные координаты относительно оптического центра камеры
        # Используем формулу: x_local = (x_pixel - cx) * distance / f
        lx = (screen_x - self.cx) * distance / self.f
        ly = (screen_y - self.cy) * distance / self.f
        lz = distance

        local_pos = np.array([lx, ly, lz])

        # 2. Переводим из локальных координат камеры в мировые.
        # Поскольку local_pos = R @ world_pos, то world_pos = R_inv @ local_pos.
        # Для матриц вращения инверсия равна транспонированию: R.T
        R = self._get_rotation_matrix()

        # Мировые координаты = Транспонированная матрица вращения * локальный вектор
        world_pos = R.T @ local_pos

        return world_pos