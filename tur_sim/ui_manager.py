import pygame
from .camera_base import CameraBase
from .widget_camera import WidgetCamera
from .widget_telemetry import WidgetTelemetry

class UIManager:
    def __init__(self, width=1000, height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Robotic Turret Control System")

        self.clock = pygame.time.Clock()
        self.running = True
        self.elements = []

        # Инициализация камеры и виджетов
        self.camera = CameraBase(640, 480)
        self.setup_ui()

    def setup_ui(self):
        # Размещаем камеру по центру-лево
        self.elements.append(WidgetCamera(20, 20, self.camera))
        # Телеметрия справа
        self.elements.append(WidgetTelemetry(680, 20, 300, 100))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # Ограничение 60 FPS
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            for el in self.elements:
                el.handle_event(event)

    def update(self):
        pass  # Здесь будет логика обновления состояний

    def draw(self):
        self.screen.fill((10, 10, 10))  # Темный фон
        for el in self.elements:
            el.draw(self.screen)
        pygame.display.flip()