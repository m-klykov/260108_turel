import pygame
from .widget_base import WidgetBase  # Предполагая структуру папок

# Цвета состояний
COLOR_BTN_NORMAL = (70, 70, 80)
COLOR_BTN_HOVER = (90, 90, 105)
COLOR_BTN_PRESSED = (40, 40, 50)
COLOR_BTN_DISABLED = (50, 50, 55)

COLOR_TEXT_NORMAL = (255, 255, 255)
COLOR_TEXT_DISABLED = (100, 100, 100)
COLOR_BORDER = (200, 200, 200)

class WidgetButton(WidgetBase):
    def __init__(self, x, y, w, h, font, text, action_release):
        super().__init__(x, y, w, h)
        self.font = font
        self.text = text  # Теперь текст может быть "UP", "DOWN", "LEFT", "RIGHT"

        # Функции обратного вызова
        self.action_release = action_release
        self.action_press = None  # По умолчанию отсутствует

        self.is_hovered = False
        self.is_pressed = False
        self.is_enabled = True

    @classmethod
    def with_press_actions(cls, x, y, w, h, smart, font, text, action_press, action_release):
        """
        Альтернативный конструктор для кнопок, реагирующих и на нажатие, и на отпускание.
        """
        instance = cls(x, y, w, h, smart, font, text, action_release)
        instance.action_press = action_press
        return instance

    def draw(self, screen):
        # 1. Определяем цвет фона в зависимости от состояния
        bg_color = COLOR_BTN_NORMAL
        text_color = COLOR_TEXT_NORMAL
        border_color = COLOR_BORDER

        if not self.is_enabled:
            bg_color = COLOR_BTN_DISABLED
            text_color = COLOR_TEXT_DISABLED
            border_color = COLOR_TEXT_DISABLED
        elif self.is_pressed:
            bg_color = COLOR_BTN_PRESSED
        elif self.is_hovered:
            bg_color = COLOR_BTN_HOVER

        # 2. Отрисовка
        # Смещение тени или рамки при нажатии для эффекта "вдавливания"
        border_width = 1 if self.is_pressed else 2

        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=5)

        if self.font:
            surf = self.font.render(self.text, True, text_color)
            rect = surf.get_rect(center=self.rect.center)
            # При нажатии чуть сдвигаем текст вниз для реалистичности
            if self.is_pressed:
                rect.y += 2
            screen.blit(surf, rect)

    def handle_event(self, event):
        if not self.is_enabled:
            self.is_pressed = False
            self.is_hovered = False
            return

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if not self.is_hovered:
                self.is_pressed = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
                # Выполняем действие при нажатии, если оно задано
                if self.action_press:
                    self.action_press()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_hovered:
                # Срабатывание только если отпустили над кнопкой, которая была нажата
                if self.action_release:
                    self.action_release()
                self.is_pressed = False