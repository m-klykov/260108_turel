from .camera_base import CameraBase
from .camera_virtual import CameraVirtual
from .motion_base import MotionCircular
from .physical_object import PhysicalObject
from .physical_world import PhysicalWorld
from .turret_model import TurretModel


class Controller:
    def __init__(self):
        self.world = PhysicalWorld()

        # Создаем цель: желтый шарик, движется по кругу на расстоянии 10-20 метров
        target_behavior = MotionCircular(center=[0, 0, 15], radius=5, speed=1.0)
        target = PhysicalObject(
            pos=[5, 0, 15], radius=0.5,
            color=(0, 255, 255), behavior=target_behavior)
        self.world.add_object(target)

        # Инициализируем виртуальную камеру, передав ей мир
        self.camera = CameraVirtual(self.world, width=640, height=480, f=500)

        # Создаем турель и отдаем ей камеру и мир
        self.turret = TurretModel(self.camera, self.world)

    def update(self, dt):
        self.world.update(dt)
        self.turret.update(dt)

    def fire(self):
        self.turret.fire()
