import cv2
import numpy as np


class ImageAnalyzer:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Настройки фильтров (BGR)
        # Желтая цель
        self.target_lower = np.array([0, 200, 200])
        self.target_upper = np.array([50, 255, 255])

        # Зеленая пуля
        self.bullet_lower = np.array([0, 200, 0])
        self.bullet_upper = np.array([100, 255, 100])

    def _find_objects(self, frame, lower, upper, obj_type):
        """Вспомогательный метод для поиска объектов по цвету"""
        mask = cv2.inRange(frame, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        found = []
        for cnt in contours:
            # Игнорируем слишком мелкий шум
            if cv2.contourArea(cnt) < 1:
                continue

            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Вычисляем примерный "радиус" (размер) на экране
                _, radius = cv2.minEnclosingCircle(cnt)

                found.append({
                    "type": obj_type,
                    "pos": (cx, cy),
                    "screen_r": int(radius)
                })
        return found

    def analyze(self, frame):
        """Основной метод анализа кадра"""
        targets = self._find_objects(frame,
                     self.target_lower, self.target_upper, "target")

        bullets = self._find_objects(frame,
                     self.bullet_lower, self.bullet_upper, "projectile")

        return targets + bullets