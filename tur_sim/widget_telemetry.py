import math

import pygame

from .controller import Controller
from .widget_base import WidgetBase

class WidgetTelemetry(WidgetBase):

    FONT_SIZE = 20
    LINE_HEIGHT = 25

    """Виджет для вывода текстовых данных"""
    def __init__(self, x, y, width, height, controller):
        super().__init__(x, y, width, height)
        self.controller : Controller = controller
        self.font = pygame.font.SysFont('Arial', self.FONT_SIZE)

    def draw(self, screen):
        pygame.draw.rect(screen, (30, 30, 30), self.rect) # Фон
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 1) # Рамка

        tc = self.controller.shots_count
        hc = self.controller.hits_count
        cc = self.controller.chits_count

        self.out_line(screen,
            f"Выстрелов: {tc} | Попало: {hc} ({hc / (tc + 1e-6):.1%})", 0)
        self.out_line(screen,
            f"попало сразу: {hc-cc} ({(hc-cc) / (hc + 1e-6):.1%})", 1)
        self.out_line(screen,
          f"yaw: {math.degrees(self.controller.camera.yaw):.1f}"+
          f" pitch: {math.degrees(self.controller.camera.pitch):.1f}",
          2)

        self.out_line(screen,
            f"Dist to target: {self.controller.get_locked_distance():0.1f}", 3)




    def out_line(self, screen, text, line):
        text_surf = self.font.render(text, True, (0, 255, 0))

        screen.blit(text_surf, (
            self.rect.x + 10,
            self.rect.y + 10 + line * self.LINE_HEIGHT))
