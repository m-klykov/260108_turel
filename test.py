import pandas as pd
import torch
import joblib

from tur_sim.ballistics_corrector import BallisticsCorrector

# Загрузка
df = pd.read_csv("data/dataset_01.csv")
# Берем 10-ю строку для примера
row = 25
test_input = df.iloc[row, 0:6].values
true_delta = df.iloc[row, 6:8].values

# Твой класс корректора

corr = BallisticsCorrector()

pred_delta = corr.get_correction(*test_input)

print(f"Истинная дельта из файла: {true_delta}")
print(f"Предсказанная ИИ дельта:  {pred_delta}")