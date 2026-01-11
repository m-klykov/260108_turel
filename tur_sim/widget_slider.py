import pygame
import math
from .widget_base import WidgetBase

# Цвета
COLOR_BG = (50, 50, 60)
COLOR_TRACK = (100, 100, 110)
COLOR_HANDLE = (200, 200, 220)
COLOR_HANDLE_HOVER = (255, 255, 255)
COLOR_TEXT = (250, 250, 250)


class WidgetSlider(WidgetBase):
    def __init__(self, x, y, w, h, font, label, min_val, max_val, initial_val, action_on_release, is_log=False):
        super().__init__(x, y, w, h)
        self.font = font
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.is_log = is_log
        self.action_on_release = action_on_release

        # Текущее значение (физическое)
        self.value = initial_val

        # Параметры отрисовки
        self.handle_w = 12
        self.is_dragging = False
        self.is_hovered = False

    def _get_pct(self):
        """Возвращает положение ползунка от 0.0 до 1.0 на основе self.value"""
        if self.is_log:
            # log(val) = log(min) + pct * (log(max) - log(min))
            return (math.log10(self.value) - math.log10(self.min_val)) / \
                (math.log10(self.max_val) - math.log10(self.min_val))
        else:
            return (self.value - self.min_val) / (self.max_val - self.min_val)

    @property
    def cur_value(self):
        return self.value

    @cur_value.setter
    def cur_value(self, value):
        self.value = value

    def _set_value_from_pct(self, pct):
        """Устанавливает self.value на основе положения ползунка 0.0-1.0"""
        pct = max(0, min(1, pct))  # Ограничение
        if self.is_log:
            # val = 10^(log(min) + pct * log(max/min))
            log_val = math.log10(self.min_val) + pct * (math.log10(self.max_val) - math.log10(self.min_val))
            self.value = 10 ** log_val
        else:
            self.value = self.min_val + pct * (self.max_val - self.min_val)

    def draw(self, screen):
        # 1. Отрисовка фона и подписи
        # pygame.draw.rect(screen, COLOR_BG, self.rect, border_radius=3)

        # Рисуем подпись и текущее значение
        val_str = f"{self.value:.4f}" if self.value < 1 else f"{self.value:.2f}"
        text_surf = self.font.render(f"{self.label}: {val_str}", True, COLOR_TEXT)
        screen.blit(text_surf, (self.rect.x, self.rect.y - 20))

        # 2. Линия трека (центр по вертикали)
        track_y = self.rect.centery
        track_rect = pygame.Rect(self.rect.x, track_y - 2, self.rect.w, 4)
        pygame.draw.rect(screen, COLOR_TRACK, track_rect, border_radius=2)

        # 3. Ползунок (handle)
        pct = self._get_pct()
        handle_x = self.rect.x + (self.rect.w - self.handle_w) * pct
        handle_rect = pygame.Rect(handle_x, self.rect.y, self.handle_w, self.rect.h)

        h_color = COLOR_HANDLE_HOVER if (self.is_hovered or self.is_dragging) else COLOR_HANDLE
        pygame.draw.rect(screen, h_color, handle_rect, border_radius=4)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_dragging:
                # Считаем относительный X внутри виджета
                rel_x = event.pos[0] - self.rect.x
                pct = rel_x / self.rect.w
                self._set_value_from_pct(pct)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_dragging = True
                # Сразу прыгаем в точку клика
                rel_x = event.pos[0] - self.rect.x
                self._set_value_from_pct(rel_x / self.rect.w)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_dragging:
                self.is_dragging = False
                # Вызываем коллбэк для обновления параметров Калмана
                if self.action_on_release:
                    self.action_on_release(self.value)