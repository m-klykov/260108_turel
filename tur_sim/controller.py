import math

import numpy as np

from .ballistics_solver import BallisticsSolver
from .camera_base import CameraBase
from .camera_virtual import CameraVirtual
from .image_analizer import ImageAnalyzer
from .motion_base import MotionCircular, MotionPointToPoint
from .physical_object import PhysicalObject
from .physical_world import PhysicalWorld
from .tracked_target import TrackedTarget
from .turret_model import TurretModel


class Controller:

    TARGET_RADIUS = 0.5 #радиус цели

    def __init__(self):
        self.world = PhysicalWorld()

        self._init_world()

        # Инициализируем виртуальную камеру, передав ей мир
        self.camera : CameraVirtual = CameraVirtual(self.world, width=640, height=480, f=500)

        # Создаем турель и отдаем ей камеру и мир
        self.turret = TurretModel(self.camera, self.world)

        self.analyzer = ImageAnalyzer(640, 480)
        self.current_detections = []

        self.locked_target_data = None  # Здесь храним данные о детекции (экранные)
        self.is_locked = False
        self.active_track : TrackedTarget = None  # Экземпляр TrackedTarget

    def _init_world(self):
        # Создаем цель: желтый шарик, движется по кругу на расстоянии 10-20 метров
        target_behavior = MotionCircular(center=[0, -1, 15], radius=5, speed=1.0)
        target = PhysicalObject(
            pos=[0, -1, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=target_behavior,
            obj_type="target"
        )
        self.world.add_object(target)

        target_behavior = MotionCircular(center=[2, -1, 15], radius=4, speed=1.5)
        target = PhysicalObject(
            pos=[0, -4, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=target_behavior,
            obj_type="target"
        )
        self.world.add_object(target)

        target = PhysicalObject(
            pos=[6, -4.7, 12], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=None,
            obj_type="target"
        )
        self.world.add_object(target)

        target_behavior = MotionPointToPoint([-4, -6, 20], [4, -6, 10], speed=1.7)
        target = PhysicalObject(
            pos=[-4, -2, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=target_behavior,
            obj_type="target"
        )
        self.world.add_object(target)

    def update(self, dt):
        # 1. Обновляем мир и турель и кеш камеры
        self.world.update(dt)

        self.turret.update(dt)

        self.camera.refresh()

        # 2. Получаем "картинку" с камеры
        frame = self.camera.get_frame()

        # 3. АНАЛИЗИРУЕМ пиксели (теперь это наш основной источник данных для ИИ)
        self.current_detections = self.analyzer.analyze(frame)

        for det in self.current_detections:
            if det["type"] == "target":
                det["distance"] = BallisticsSolver.estimate_distance(
                    det["screen_r"], self.TARGET_RADIUS, self.camera.f
                )

        self._update_target_lock()

        # Для отладки можно выводить количество найденных объектов
        # if self.current_detections:
        #    print(f"Detected: {len(self.current_detections)} objects")

    def fire(self):
        self.turret.fire()

    def set_target_by_pixel(self, x, y):
        """Первичный захват по клику мыши"""
        self.clear_target()
        best_target = None
        min_dist = 40  # Радиус поиска цели вокруг клика

        for det in self.current_detections:
            if det["type"] == "target":
                dist = np.hypot(det["pos"][0] - x, det["pos"][1] - y)
                if dist < min_dist:
                    min_dist = dist
                    best_target = det

        if best_target:
            self.handle_target_lock(best_target)
            print(f"Target locked at {self.locked_target_data['pos']}")

    def clear_target(self):
        self.locked_target_data = None
        self.is_locked = False
        self.active_track = None

    def move_turret_to_pixel(self, x, y):
        """Сброс захвата и ручной поворот в точку"""
        self.clear_target()
        new_yaw, new_pitch = self.camera.get_angles_from_pixel(x, y)
        self.turret.set_target_angles(new_yaw, new_pitch)

    def handle_target_lock(self, detection):
        self.locked_target_data = detection
        self.is_locked = True

        # Переводим экранные координаты в мировые
        dist = BallisticsSolver.estimate_distance(
            detection["screen_r"], self.TARGET_RADIUS, self.camera.f
        )

        if self.active_track is None:
            # Создаем новый трек
            self.active_track = TrackedTarget(
                1,
                detection["pos"][0],
                detection["pos"][1],
                dist,
                self.camera
            )
        else:
            # Обновляем существующий
            # Передаем сырые данные в трек для стабилизации
            self.active_track.update_with_screen_data(
                detection["pos"][0],
                detection["pos"][1],
                dist,
                self.camera
            )

    def _update_target_lock(self):
        if self.is_locked and self.locked_target_data:
            new_lock = None
            min_dist = 50  # Максимальный прыжок цели между кадрами в пикселях

            last_x, last_y = self.locked_target_data["pos"]

            for det in self.current_detections:
                if det["type"] == "target":
                    dist = np.hypot(det["pos"][0] - last_x, det["pos"][1] - last_y)
                    if dist < min_dist:
                        min_dist = dist
                        new_lock = det

            if new_lock:
                # Цель найдена, обновляем данные
                self.handle_target_lock(new_lock)

                # наводимся с учетом дистанции
                self._turret_to_target()

            else:
                # Цель потеряна (ушла за экран или скрылась)
                pass
                # self.clear_target()

    def _turret_to_target(self):
        if not self.active_track: return

        """наводимся на ту цель"""
        # Наводим турель на обновленные координаты
        # 2. Запрашиваем решение для стрельбы
        aim_point = self.active_track.get_fire_solution(
            shooter_pos= np.array([0, 0, 0]),
            projectile_speed= self.turret.projectile_speed,
            g= BallisticsSolver.G
        )

        # 3. Переводим мировую точку прицеливания в углы для турели
        # (Используем atan2 для Yaw и Pitch)
        target_yaw = math.atan2(aim_point[0], aim_point[2])
        target_pitch = -math.atan2(aim_point[1], np.hypot(aim_point[0], aim_point[2]))

        self.turret.set_target_angles(target_yaw, target_pitch)

    def is_active_target(self,det_target):
        """проверим, являктся ли эта цель захваченой"""
        if self.is_locked:
            return det_target["pos"] == self.locked_target_data["pos"]
        else:
            return False

    def get_locked_distance(self):
        if self.is_locked:
            return self.locked_target_data["distance"]
        else:
            return 0.0