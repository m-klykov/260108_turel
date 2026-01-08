import numpy as np
import pygame

# --- СЛОЙ ОБОРУДОВАНИЯ (Hardware Layer) ---

class CameraBase:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height

    def get_frame(self):
        """Возвращает кадр в формате OpenCV (BGR numpy array)"""
        # Пока просто генерируем черный кадр
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        return frame