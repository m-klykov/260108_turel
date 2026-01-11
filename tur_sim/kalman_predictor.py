import numpy as np

class KalmanPredictor:
    def __init__(self, start_pos):
        # Состояние: [x, y, z, vx, vy, vz, ax, ay, az]
        self.X = np.zeros(9)
        self.X[0:3] = start_pos
        self.P = np.eye(9) * 1.0

        # Настраиваем Q индивидуально
        # Специфическая настройка Q:
        self.Q = np.eye(9)
        self.Q[0:3, 0:3] *= 0.01  # Позиция (очень верим модели)
        self.Q[3:6, 3:6] *= 0.1  # Скорость (верим модели)
        self.Q[6:9, 6:9] *= 8.0  # УСКОРЕНИЕ (даем полную свободу меняться!)

        # Если точка всё еще отстает, уменьшаем R (больше верим камере)
        self.R = np.eye(3) * 0.008

        # Мы извлекаем x, y, z и игнорируем остальное
        self.H = np.zeros((3, 9))
        self.H[0:3, 0:3] = np.eye(3)

        # self.X = np.array([start_pos[0], start_pos[1], start_pos[2], 0, 0, 0], dtype=float)
        #
        # self.P = np.eye(6) * 1.0  # Уверенность
        # self.Q = np.eye(6) * 0.5  # Шум процесса (насколько цель непредсказуема)
        # self.R = np.eye(3) * 0.01  # Шум замера (насколько дергается детекция)
        #
        # self.H = np.zeros((3, 6))
        # self.H[0:3, 0:3] = np.eye(3)

    def update(self, z, dt):
        if dt <= 0: return self.X

        # 1. Prediction
        # F = np.eye(6)
        # F[0, 3] = dt;
        # F[1, 4] = dt;
        # F[2, 5] = dt

        F = np.eye(9)
        # Скорость влияет на позицию
        F[0, 3] = F[1, 4] = F[2, 5] = dt
        # Ускорение влияет на скорость
        F[3, 6] = F[4, 7] = F[5, 8] = dt
        # Ускорение влияет на позицию (0.5 * dt^2)
        F[0, 6] = F[1, 7] = F[2, 8] = 0.5 * dt ** 2

        self.X = F @ self.X
        self.P = F @ self.P @ F.T + self.Q

        # 2. Correction
        z = np.array(z, dtype=float)
        y = z - (self.H @ self.X)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.X = self.X + K @ y
        self.P = (np.eye(9) - K @ self.H) @ self.P

        return self.X

    def predict(self, t_ahead):
        # Добавляем компоненту ускорения: x + v*t + 0.5*a*t^2
        pos = self.X[0:3]
        vel = self.X[3:6]
        acc = self.X[6:9]
        return pos + vel * t_ahead + 0.5 * acc * (t_ahead ** 2)