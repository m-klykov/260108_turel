class PhysicalWorld:
    def __init__(self):
        self.objects = []
        self.last_time = 0

    def add_object(self, obj):
        self.objects.append(obj)

    def update(self, dt):
        for obj in self.objects:
            obj.update(dt)
        # Здесь в будущем будет проверка коллизий (попаданий)