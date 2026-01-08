import numpy as np

from .camera_base import CameraBase
from .camera_virtual import CameraVirtual
from .image_analizer import ImageAnalyzer
from .motion_base import MotionCircular
from .physical_object import PhysicalObject
from .physical_world import PhysicalWorld
from .turret_model import TurretModel


class Controller:
    def __init__(self):
        self.world = PhysicalWorld()

        self._init_world()

        # Инициализируем виртуальную камеру, передав ей мир
        self.camera = CameraVirtual(self.world, width=640, height=480, f=500)

        # Создаем турель и отдаем ей камеру и мир
        self.turret = TurretModel(self.camera, self.world)

        self.analyzer = ImageAnalyzer(640, 480)
        self.current_detections = []

        self.locked_target_data = None  # Здесь храним данные о детекции (экранные)
        self.is_locked = False

    def _init_world(self):
        # Создаем цель: желтый шарик, движется по кругу на расстоянии 10-20 метров
        target_behavior = MotionCircular(center=[0, -1, 15], radius=5, speed=1.0)
        target = PhysicalObject(
            pos=[0, -1, 15], radius=0.5,
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

        self._update_target_lock()

        # Для отладки можно выводить количество найденных объектов
        # if self.current_detections:
        #    print(f"Detected: {len(self.current_detections)} objects")

    def fire(self):
        self.turret.fire()

    def set_target_by_pixel(self, x, y):
        """Первичный захват по клику мыши"""
        best_target = None
        min_dist = 40  # Радиус поиска цели вокруг клика

        for det in self.current_detections:
            if det["type"] == "target":
                dist = np.hypot(det["pos"][0] - x, det["pos"][1] - y)
                if dist < min_dist:
                    min_dist = dist
                    best_target = det

        if best_target:
            self.locked_target_data = best_target
            self.is_locked = True
            print(f"Target locked at {self.locked_target_data['pos']}")
        else:
            self.is_locked = False

    def clear_target(self):
        self.locked_target_data = None
        self.is_locked = False

    def move_turret_to_pixel(self, x, y):
        """Сброс захвата и ручной поворот в точку"""
        self.clear_target()
        new_yaw, new_pitch = self.camera.get_angles_from_pixel(x, y)
        self.turret.set_target_angles(new_yaw, new_pitch)

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
                self.locked_target_data = new_lock
                # Наводим турель на обновленные координаты
                tx, ty = self.locked_target_data["pos"]
                ny, np_ = self.camera.get_angles_from_pixel(tx, ty)
                self.turret.set_target_angles(ny, np_)
            else:
                # Цель потеряна (ушла за экран или скрылась)
                # self.is_locked = False # Можно либо сбросить, либо оставить старые коорд.
                pass

    def is_active_target(self,det_target):
        """проверим, являктся ли эта цель захваченой"""
        if self.is_locked:
            return det_target["pos"] == self.locked_target_data["pos"]
        else:
            return False