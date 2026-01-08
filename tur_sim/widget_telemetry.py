import pygame
from datetime import datetime

from .controller import Controller
from .widget_base import WidgetBase

class WidgetTelemetry(WidgetBase):
    """Виджет для вывода текстовых данных"""
    def __init__(self, x, y, width, height, controller):
        super().__init__(x, y, width, height)
        self.controller : Controller = controller
        self.font = pygame.font.SysFont('Arial', 18)

    def draw(self, screen):
        pygame.draw.rect(screen, (30, 30, 30), self.rect) # Фон
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 1) # Рамка

        time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        text_surf = self.font.render(f"System Time: {time_str}", True, (0, 255, 0))
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))
