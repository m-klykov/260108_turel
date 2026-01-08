import numpy as np
import pygame
import cv2
from .widget_base import WidgetBase
from .camera_base import CameraBase

class WidgetCamera(WidgetBase):
    """Виджет для отображения потока с камеры"""

    def __init__(self, x, y, camera):
        super().__init__(x, y, camera.width, camera.height)
        self.camera : CameraBase = camera

    def draw(self, screen):
        # 1. Получаем кадр от камеры
        frame = self.camera.get_frame()

        # 2. Конвертируем BGR (OpenCV) в RGB (Pygame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 3. Создаем Surface из массива (нужно транспонировать оси для Pygame)
        # Pygame ожидает (width, height), а numpy выдает (height, width)
        surface = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))

        # 4. Отрисовка
        screen.blit(surface, self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)  # Рамка

        # 3. Рисуем прицел (Crosshair)
        center_x, center_y = self.rect.center
        color = (255, 0, 0)  # Красный прицел
        length = 20  # Длина линий прицела
        gap = 5  # Пропуск в самом центре (опционально)

        # Горизонтальная линия (левая и правая части)
        pygame.draw.line(screen, color, (center_x - length, center_y), (center_x - gap, center_y), 2)
        pygame.draw.line(screen, color, (center_x + gap, center_y), (center_x + length, center_y), 2)

        # Вертикальная линия (верхняя и нижняя части)
        pygame.draw.line(screen, color, (center_x, center_y - length), (center_x, center_y - gap), 2)
        pygame.draw.line(screen, color, (center_x, center_y + gap), (center_x, center_y + length), 2)

        # Точка в центре (необязательно)
        pygame.draw.circle(screen, color, (center_x, center_y), 2)

        # 4. Внешняя рамка виджета
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)