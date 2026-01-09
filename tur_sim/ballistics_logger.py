import csv
import os
import numpy as np

class BallisticsLogger:
    def __init__(self, filename="ballistics_dataset.csv"):
        self.filename = filename
        self.headers = [
            "err_yaw", "err_pitch",
            "v_yaw", "v_pitch",
            "dist", "turret_pitch",
            "miss_x", "miss_y", "miss_z",
            "is_hit"
        ]
        self._prepare_file()

    def _prepare_file(self):
        """Создает файл с заголовками, если он еще не существует"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_shot(self, state, miss_vector, target_radius):
        """
        Записывает результат выстрела.
        state: вектор входных данных для нейросети
        miss_vector: 3D вектор промаха в точке CPA
        target_radius: радиус цели для определения попадания
        """
        miss_dist = np.linalg.norm(miss_vector)
        is_hit = 1 if miss_dist <= target_radius else 0

        # Собираем строку: данные состояния + координаты промаха + флаг попадания
        row = list(state) + list(miss_vector) + [is_hit]

        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        return is_hit, miss_dist