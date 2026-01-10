import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# 1. Загрузка данных
try:
    fn = "data/dataset_01.csv"
    df = pd.read_csv(fn)
except FileNotFoundError:
    print(f"Файл {fn} не найден!")
    exit()

# Определяем входы и выходы
features = ["err_yaw", "err_pitch", "v_yaw", "v_pitch", "dist", "turret_pitch"]
targets = ["delta_yaw", "delta_pitch"]

X = df[features]
y = df[targets]

# 2. Обучение модели для анализа
# Используем 100 деревьев, чтобы получить стабильный результат
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# 3. Извлекаем важность
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]

# 4. Визуализация
plt.figure(figsize=(10, 6))
plt.title("Важность признаков для баллистической коррекции")
plt.bar(range(X.shape[1]), importances[indices], align="center")
plt.xticks(range(X.shape[1]), [features[i] for i in indices], rotation=45)
plt.ylabel("Доля влияния (0.0 - 1.0)")
plt.tight_layout()
plt.show()

# Вывод в консоль
print("Рейтинг полезности полей:")
for i in indices:
    print(f"{features[i]}: {importances[i]:.4f}")