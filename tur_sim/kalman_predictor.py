import numpy as np

class KalmanPredictor:
    DEF_Q_POS = 0.01

    DEF_Q_VAL = 0.1

    DEF_Q_ACC = 8.0

    MIN_Q = 0.01
    MAX_Q = 100.0

    DEF_R_NOISE = 0.2
    MIN_R_NOISE = 0.0001
    MAX_R_NOISE = 0.5

    def __init__(self,
         start_pos,
         q_pos=DEF_Q_POS,
         q_vel=DEF_Q_VAL,
         q_acc=DEF_Q_ACC,
         r_noise=DEF_R_NOISE
    ):
        # 1. Состояние и матрицы
        self.X = np.zeros(9)
        self.X[0:3] = start_pos
        self.P = np.eye(9) * 1.0
        self.H = np.zeros((3, 9))
        self.H[0:3, 0:3] = np.eye(3)

        # 2. Сохраняем параметры во внутренние переменные (для чтения слайдерами)
        self._q_pos = q_pos
        self._q_vel = q_vel
        self._q_acc = q_acc
        self._r_noise = r_noise

        # 3. Инициализируем матрицы Q и R
        self.Q = np.eye(9)
        self.R = np.eye(3)
        self._update_matrices()

    def _update_matrices(self):
        """Внутренний метод для пересчета диагоналей матриц Q и R"""
        # Обновляем Q
        self.Q[0:3, 0:3] = np.eye(3) * self._q_pos
        self.Q[3:6, 3:6] = np.eye(3) * self._q_vel
        self.Q[6:9, 6:9] = np.eye(3) * self._q_acc

        # Обновляем R
        self.R = np.eye(3) * self._r_noise

    def set_params(self,params):
        """динамисески применить настройки из асой массива"""
        if 'q_ass' in params:
            self.q_acc = params['q_acc']

        if 'r_noise' in params:
            self.r_noise = params['r_noise']

    # --- Геттеры (чтобы Pygame виджеты могли считать текущее состояние) ---

    @property
    def q_pos(self): return self._q_pos

    @property
    def q_vel(self): return self._q_vel

    @property
    def q_acc(self): return self._q_acc

    @property
    def r_noise(self): return self._r_noise

    # --- Сеттеры (вызываются при движении ползунков) ---
    @q_pos.setter
    def q_pos(self, val):
        self._q_pos = val
        self._update_matrices()

    @q_vel.setter
    def q_vel(self, val):
        self._q_vel = val
        self._update_matrices()

    @q_acc.setter
    def q_acc(self, value):
        self._q_acc = val
        self._update_matrices()

    @r_noise.setter
    def r_noise(self, val):
        # Ограничиваем снизу, чтобы не вызвать деление на ноль в инверсии матриц
        self._r_noise = max(val, 1e-6)
        self._update_matrices()


    def update(self, z, dt):
        if dt <= 0: return self.X

        # Прогноз (F-матрица для равноускоренного движения)
        F = np.eye(9)
        F[0:3, 3:6] = np.eye(3) * dt  # x = x + v*dt
        F[3:6, 6:9] = np.eye(3) * dt  # v = v + a*dt
        F[0:3, 6:9] = np.eye(3) * (0.5 * dt ** 2)  # x = x + 0.5*a*dt^2

        self.X = F @ self.X
        self.P = F @ self.P @ F.T + self.Q

        # Коррекция
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