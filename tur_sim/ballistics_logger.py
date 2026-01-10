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
            "delta_yaw", "delta_pitch",
            "is_hit"
        ]
        self._prepare_file()

    def _prepare_file(self):
        """Создает файл с заголовками, если он еще не существует"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_shot(self, state, miss_angles, is_hit):
        """
        Записывает результат выстрела.
        state: вектор входных данных для нейросети
        miss_angles: (delta_yaw, delta_pitch)
        is_hit: факт попадания
        """

        # Собираем строку: данные состояния + координаты промаха + флаг попадания
        row = list(state) + list(miss_angles) + [is_hit]

        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
