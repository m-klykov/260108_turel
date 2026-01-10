import torch
import torch.nn as nn
import joblib
import numpy as np

# Описываем ту же архитектуру, что была при обучении
class BallisticsNet(nn.Module):
    def __init__(self):
        super(BallisticsNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 128),  # Больше нейронов
            nn.LeakyReLU(),  # Более гибкая функция активации
            nn.Linear(128, 128),
            nn.LeakyReLU(),
            nn.Linear(128, 64),
            nn.LeakyReLU(),
            nn.Linear(64, 2)
        )

    def forward(self, x):
        return self.net(x)


class BallisticsCorrector:
    MODEL_PATH = "data/ballistics_model.pth"
    SCALLER_X_PATH = "data/scaler_x.pkl"
    SCALLER_Y_PATH = "data/scaler_y.pkl"

    def __init__(self):
        self.is_ready = False
        try:
            # 1. Загружаем скалеры
            self.scaler_x = joblib.load( self.SCALLER_X_PATH )
            self.scaler_y = joblib.load( self.SCALLER_Y_PATH )

            # 2. Загружаем модель
            self.model = BallisticsNet()
            self.model.load_state_dict(torch.load( self.MODEL_PATH))
            self.model.eval()  # Режим предсказания (отключает dropout и т.д.)

            self.is_ready = True
            print("AI Corrector: Loaded successfully")
        except Exception as e:
            print(f"AI Corrector Error: Could not load model. {e}")

    def get_correction(self, err_yaw, err_pitch, v_yaw, v_pitch, dist, turret_pitch):
        """
        Принимает текущее состояние и возвращает (d_yaw, d_pitch) в радианах.
        """
        if not self.is_ready:
            return 0.0, 0.0

        # Формируем вектор входа в том же порядке, что и в CSV
        state = np.array([[
            err_yaw, err_pitch, v_yaw, v_pitch, dist, turret_pitch
        ]])

        # 1. Масштабируем вход (Scale X)
        state_scaled = self.scaler_x.transform(state)

        # 2. Прогоняем через нейросеть
        with torch.no_grad():
            input_tensor = torch.FloatTensor(state_scaled)
            output_scaled = self.model(input_tensor).numpy()

        # 3. Обратное масштабирование выхода (Inverse Scale Y)
        # Получаем значения в радианах
        correction = self.scaler_y.inverse_transform(output_scaled)

        # correction — это [[d_yaw, d_pitch]]
        return correction[0][0], correction[0][1]