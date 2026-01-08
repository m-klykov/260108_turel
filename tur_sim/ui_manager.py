import pygame
from .camera_base import CameraBase
from .widget_camera import WidgetCamera
from .widget_telemetry import WidgetTelemetry
from .controller import Controller

class UIManager:
    def __init__(self, controller, width=1000, height=600):

        self.controller : Controller = controller

        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Robotic Turret Control System")

        self.clock = pygame.time.Clock()
        self.running = True
        self.elements = []

        # Инициализация камеры и виджетов
        self.setup_ui()

    def setup_ui(self):
        # Размещаем камеру по центру-лево
        self.elements.append(WidgetCamera(
            20, 20,
            self.controller.camera))

        # Телеметрия справа
        self.elements.append(WidgetTelemetry(
            680, 20, 300, 100,
            self.controller))

    def run(self):
        while self.running:
            # Получаем время кадра в миллисекундах и переводим в секунды
            # tick(60) гарантирует, что цикл не выполнится быстрее 60 раз в секунду
            dt = self.clock.tick(60) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.controller.fire()

            for el in self.elements:
                el.handle_event(event)

    def update(self,dt):

        keys = pygame.key.get_pressed()

        # Прямое управление аоворотом турели
        dx, dy = 0, 0

        if keys[pygame.K_LEFT]:  dx = - dt
        if keys[pygame.K_RIGHT]: dx =  dt
        if keys[pygame.K_UP]:    dy = - dt
        if keys[pygame.K_DOWN]:  dy = dt

        self.controller.turret.turn(dx,dy)

        self.controller.update(dt)



    def draw(self):
        self.screen.fill((10, 10, 10))  # Темный фон
        for el in self.elements:
            el.draw(self.screen)
        pygame.display.flip()