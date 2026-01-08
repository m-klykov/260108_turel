import numpy as np
import pygame
import cv2

from .controller import Controller
from .widget_base import WidgetBase
from .camera_base import CameraBase

class WidgetCamera(WidgetBase):
    """Виджет для отображения потока с камеры"""

    def __init__(self, x, y, controller):
        camera = controller.camera

        super().__init__(x, y, camera.width, camera.height)

        self.controller : Controller = controller
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

        self._draw_cross(screen)

        self._draw_detections(screen)

        # 4. Внешняя рамка виджета
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)

    def _draw_cross(self, screen):
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

    def _draw_detections(self, screen):
        # Добавляем отрисовку "рамок захвата" из анализатора
        # Предположим, контроллер доступен виджету
        detections = self.controller.current_detections

        for det in detections:
            x, y = det["pos"]
            r = det["screen_r"] + 1  # Немного увеличим рамку для красоты

            # Рисуем квадрат вокруг объекта (экранные координаты виджета)
            rect_to_draw = pygame.Rect(
                self.rect.x + x - r,
                self.rect.y + y - r,
                r * 2, r * 2
            )

            # Выбор цвета
            if self.controller.is_active_target(det):
                color = (0, 0, 255)  # Синий для захвата
                thickness = 3
            else:
                color = (255, 255, 255) if det["type"] == "target" else (0, 255, 0)
                thickness = 1

            pygame.draw.rect(screen, color, rect_to_draw, thickness)

    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Проверяем, попал ли клик в область виджета камеры
            if self.rect.collidepoint(mouse_pos):
                # Координаты клика относительно начала виджета
                local_x = mouse_pos[0] - self.rect.x
                local_y = mouse_pos[1] - self.rect.y

                if event.button == 1:  # Левая кнопка - ЗАХВАТ
                    self.controller.set_target_by_pixel(local_x, local_y)
                elif event.button == 3:  # Правая кнопка - РУЧНОЙ ПОВОРОТ
                    self.controller.move_turret_to_pixel(local_x, local_y)