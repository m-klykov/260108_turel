import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib  # для сохранения скалера

# 1. Загрузка данных
df = pd.read_csv("data/dataset_01.csv")

print("Колонки в файле:", df.columns.tolist())

# Входные параметры (Features)
X = df[["err_yaw", "err_pitch", "v_yaw", "v_pitch", "dist", "turret_pitch"]].values
# Целевые поправки (Labels)
y = df[["delta_yaw", "delta_pitch"]].values

# 2. Масштабирование (Scale)
scaler_x = StandardScaler()
scaler_y = StandardScaler()

X_scaled = scaler_x.fit_transform(X)
y_scaled = scaler_y.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.2)


# 3. Архитектура нейросети
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


model = BallisticsNet()
criterion = nn.MSELoss()
# Уменьшаем lr до 0.0005 для более точной подстройки
optimizer = optim.Adam(model.parameters(), lr=0.0005)

# 4. Цикл обучения
epochs = 2000
for epoch in range(epochs):
    inputs = torch.FloatTensor(X_train)
    targets = torch.FloatTensor(y_train)

    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()

    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.6f}")

# 5. Сохранение
torch.save(model.state_dict(), "ballistics_model.pth")
joblib.dump(scaler_x, "scaler_x.pkl")
joblib.dump(scaler_y, "scaler_y.pkl")
print("Обучение завершено. Модель сохранена.")