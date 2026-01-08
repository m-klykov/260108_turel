import numpy as np

class PhysicalWorld:
    def __init__(self):
        self.objects = []
        self.last_time = 0
        self.score = 0

    def add_object(self, obj):
        self.objects.append(obj)

    def update(self, dt):
        for obj in self.objects:
            obj.update(dt)

        # Здесь в будущем будет проверка коллизий (попаданий)
        # 2. Проверяем столкновения (пули с целями)
        # Для простоты: пуля — это то, у чего маленький радиус и есть скорость
        projectiles = [o for o in self.objects if o.radius < 0.2 and not o.is_dead]
        targets = [o for o in self.objects if o.radius >= 0.2 and not o.is_dead]

        for p in projectiles:
            for t in targets:
                # Вычисляем расстояние в 3D
                dist = np.linalg.norm(p.pos - t.pos)
                if dist < (p.radius + t.radius):
                    p.is_dead = True
                    # t.is_dead = True # Можно уничтожать цель, а можно просто засчитать хит
                    self.score += 1
                    print(f"HIT! Score: {self.score}")

        # 3. Удаляем "мертвые" объекты
        self.objects = [o for o in self.objects if not o.is_dead]