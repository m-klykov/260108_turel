# --- СЛОЙ ИНТЕРФЕЙСА (UI Layer) ---
import pygame


class WidgetBase:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        pass

    def handle_event(self, event):
        pass