import math
import numpy as np

from .ballistics_corrector import BallisticsCorrector
from .ballistics_logger import BallisticsLogger
from .ballistics_solver import BallisticsSolver
from .camera_virtual import CameraVirtual
from .image_analizer import ImageAnalyzer
from .motion_base import MotionCircular, MotionPointToPoint, MotionSpline
from .physical_object import PhysicalObject
from .physical_world import PhysicalWorld
from .tracked_target import TrackedTarget
from .turret_model import TurretModel


class Controller:

    TARGET_RADIUS = 0.5 #радиус цели

    # Состояния автомата
    STATE_MANUAL = "MANUAL"  # ручная работа
    STATE_SEARCHING = "SEARCHING"  # Цели нет, смотрим в центр
    STATE_TRACKING = "TRACKING"  # Цель захвачена, наводимся
    STATE_WAIT_CPA = "WAIT_CPA"  # Пуля в воздухе, ждем момента сближения

    LOGGING_SHOTS = False # пишеи ли инфу для нейромети в файл
    LOGGING_FILE = 'dataset_02.csv'

    AUTO_SHOTTING = False # выполняем ли автоматическую стрельбу

    USE_AI = False # исаоользуем нейросеть

    USE_SERIES = False # использовать серийнцю стрельбу

    def __init__(self):
        self.world = PhysicalWorld()

        self._init_world() # _v02

        # Инициализируем виртуальную камеру, передав ей мир
        self.camera : CameraVirtual = CameraVirtual(self.world, width=640, height=480, f=500)

        # Создаем турель и отдаем ей камеру и мир
        self.turret = TurretModel(self.camera, self.world)

        self.analyzer = ImageAnalyzer(640, 480)
        self.current_detections = []

        self.locked_target_data = None  # Здесь храним данные о детекции (экранные)
        self.is_locked = False
        self.active_track : TrackedTarget = None  # Экземпляр TrackedTarget

        # Данные для обучения и статистики
        self.active_shot = None  # Информация о летящей пуле
        self.shots_count = 0
        self.hits_count = 0
        self.chits_count = 0

        self.fire_wait_ticks = 50
        self.fire_wait_cnt = 0

        self.lost_targ_cnt = 0

        if self.AUTO_SHOTTING:
            self.state = self.STATE_SEARCHING
        else:
            self.state = self.STATE_MANUAL

        if self.LOGGING_SHOTS:
            self.logger = BallisticsLogger(self.LOGGING_FILE)

        if self.USE_AI:
            self.corrector = BallisticsCorrector()

        # --- НОВОЕ ДЛЯ ОБРАТНОЙ СВЯЗИ ---
        self.feedback_offset_yaw = 0.0
        self.feedback_offset_pitch = 0.0
        self.correction_series_cnt = 0
        self.MAX_CORRECTION_ATTEMPTS = 2  # Макс кол-во быстрых дострелов
        self.K_FEEDBACK = 0.8  # Насколько сильно доверяем промаху (0.8 = 80%)

    def set_auto_mode(self, tutn_on):
        if tutn_on:
            self.state = self.STATE_SEARCHING
        else:
            self.state = self.STATE_MANUAL

    def series_stop(self):
        """остановка серийной стрельбы c автокоррекциуй"""
        self.feedback_offset_yaw = 0.0
        self.feedback_offset_pitch = 0.0
        self.correction_series_cnt = 0

    def _init_world_v01(self):
        # Создаем цель: желтый шарик, движется по кругу на расстоянии 10-20 метров
        target_behavior = MotionCircular(center=[0, -1, 15], radius=5, speed=1.0)
        target = PhysicalObject(
            pos=[0, -1, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=target_behavior,
            obj_type="target"
        )
        self.world.add_object(target)

        target_behavior = MotionCircular(center=[2, -1, 15], radius=4, speed=1.5)
        target = PhysicalObject(
            pos=[0, -4, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=target_behavior,
            obj_type="target"
        )
        self.world.add_object(target)

        target = PhysicalObject(
            pos=[6, -4.7, 12], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=None,
            obj_type="target"
        )
        self.world.add_object(target)

        target_behavior = MotionPointToPoint([-4, -6, 20], [4, -6, 10], speed=1.7)
        target = PhysicalObject(
            pos=[-4, -2, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=target_behavior,
            obj_type="target"
        )
        self.world.add_object(target)

    def _init_world_v02(self):
        for i in range(5):
            target_behavior = MotionPointToPoint(
                [-4, -(1 + i*2), 20],
                [4, -(1 + i*2), 20],
                i*0.6)

            target = PhysicalObject(
                pos=[0, 10, 20], radius=self.TARGET_RADIUS,
                color=(0, 255, 255), behavior=target_behavior,
                obj_type="target"
            )
            self.world.add_object(target)



    def _init_world(self):
        # Границы: X от -30 до 30, Y от 5 до 20, Z от 40 до 80
        min_b = [-8, -8, 5]
        max_b = [8, -1, 30]

        spline_behavior = MotionSpline(min_b, max_b, num_points=50, speed=5.0)

        self.target_obj = PhysicalObject(
            pos=[0, -1, 15], radius=self.TARGET_RADIUS,
            color=(0, 255, 255), behavior=spline_behavior,
            obj_type="target"
        )
        self.world.add_object(self.target_obj)



    def update(self, dt):
        # 1. Обновляем мир и турель и кеш камеры
        self.world.update(dt)

        self.turret.update(dt)

        self.camera.refresh()

        # 2. Получаем "картинку" с камеры
        frame = self.camera.get_frame()

        # 3. АНАЛИЗИРУЕМ пиксели (теперь это наш основной источник данных для ИИ)
        self.current_detections = self.analyzer.analyze(frame)

        for det in self.current_detections:
            if det["type"] == "target":
                det["distance"] = BallisticsSolver.estimate_distance(
                    det["screen_r"], self.TARGET_RADIUS, self.camera.f
                )

        self._update_target_lock()

        # Логика конечного автомата
        if self.state == self.STATE_SEARCHING:
            self._state_searching()

        elif self.state == self.STATE_TRACKING:
            self._state_tracking(dt)

        elif self.state == self.STATE_WAIT_CPA:
            self._state_wait_cpa()

        # Для отладки можно выводить количество найденных объектов
        # if self.current_detections:
        #    print(f"Detected: {len(self.current_detections)} objects")

    def _state_searching(self):
        """1. Цели не видно — повернуться в 0,0 и ждать."""
        if self.is_locked:
            self.state = self.STATE_TRACKING
            print("Цель активна, идет трекинг")
            return

        # Ищем любую цель для захвата
        targets = [d for d in self.current_detections if d["type"] == "target"]
        if targets:
            # Берем первую попавшуюся
            self.handle_target_lock(targets[0])
            self.state = self.STATE_TRACKING
            # взводим тамер
            self.fire_wait_cnt = self.fire_wait_ticks
            print("Цель найлена! Ативируем.")
        else:
             # Возвращаем турель в нейтраль
            self.turret.set_target_angles(0, 0)

    def _state_tracking(self, dt):
        """2-3. Цель захвачена, наводимся. Если пули нет — стреляем."""
        if not self.is_locked:
            self.state = self.STATE_SEARCHING
            print("Цель потеряна! Ищем.")
            return

        if self.active_shot is not None:
            self.state = self.STATE_WAIT_CPA
            print("Выстрел не закончен! Ждем резкльтат.")
            return

        if self.fire_wait_cnt > 0:
            # ждем
            self.fire_wait_cnt -= 1
        elif not self.turret.limited_turn:
            # стреляем
            self._perform_automated_shot()

    def _perform_automated_shot(self):
        """Запись параметров и выстрел."""
        # Снимаем состояние ПЕРЕД выстрелом
        state = self.get_nn_state()

        bullet = self.turret.fire()
        if bullet:
            self.active_shot = {
                "bullet": bullet,
                "state": state,
                "min_dist": float('inf'),
                "required_delta": None,
                "target_pos_at_shot": self.active_track.position.copy()
            }
            self.state = self.STATE_WAIT_CPA
            print("Выстрел.")
            self.shots_count += 1
        else:
            self.active_shot = None


    def _state_wait_cpa(self):
        """4-5. Отслеживаем пулю и ее сближение."""
        if not self.active_shot:
            self.state = self.STATE_SEARCHING
            print("Выстрел обнулен! Ищем.")
            return

        shot = self.active_shot
        bullet = shot["bullet"]
        target = self.target_obj

        # Берем текущее положение цели (истинное из трекера)

        rel_pos = bullet.pos - target.pos
        current_dist = np.linalg.norm(rel_pos)

        # Ищем точку минимального сближения (CPA)
        if current_dist < shot["min_dist"] and not bullet.is_dead:
            shot["min_dist"] = current_dist

            # Получаем углы обоих объектов относительно того, КУДА СМОТРЕЛА камера
            b_yaw, b_pitch = self.camera.get_angles_from_world_point(bullet.pos)
            t_yaw, t_pitch = self.camera.get_angles_from_world_point(target.pos)

            # Искомая дельта (на сколько промахнулись в радианах)
            # Если t_yaw > b_yaw, значит цель была правее пули -> нужно добавить yaw
            delta_yaw = t_yaw - b_yaw
            delta_pitch = t_pitch - b_pitch

            shot["required_delta"] =(delta_yaw, delta_pitch)
        else:
            # Расстояние начало расти — пуля пролетела мимо цели
            self._finalize_shot(shot)
            self.active_shot = None

            # Если цель всё еще на экране, продолжаем трекинг, иначе в поиск
            if self.is_locked:
                self.state = self.STATE_TRACKING
                # взводим тамер
                self.fire_wait_cnt = self.fire_wait_ticks
                print("Готовим следующий выстрел.")
            else:
                self.state =self.STATE_SEARCHING
                print("Ищем цель.")


    def _finalize_shot(self, shot):
        """Вызывается, когда пуля прошла точку CPA"""
        #Логгер берет на себя всю грязную работу по записи
        is_hit = shot["min_dist"] < self.TARGET_RADIUS + self.turret.BULLET_RADIUS

        if self.LOGGING_SHOTS:
            self.logger.log_shot(
                shot["state"],
                shot["required_delta"],
                is_hit
            )

        self.shots_count += 1
        if is_hit:
            self.hits_count  += 1
            # Попали! Сбрасываем серию коррекций и офсеты
            if self.correction_series_cnt>0:
                self.chits_count += 1
                print(f"ПОПАДАНИЕ с коррекцией!.")
            else:
                print(f"ПОПАДАНИЕ балистикой!.")
            self.series_stop()
        elif self.USE_SERIES:
            try:
                # ПРОМАХ. Считаем поправку
                d_yaw, d_pitch = shot["required_delta"]
            except:
                d_yaw, d_pitch = 0, 0

            if self.correction_series_cnt < self.MAX_CORRECTION_ATTEMPTS:
                # Добавляем ошибку к текущему смещению
                fb = self.K_FEEDBACK
                self.feedback_offset_yaw = self.feedback_offset_yaw*(1-fb) + d_yaw * fb
                self.feedback_offset_pitch = self.feedback_offset_pitch*(1-fb) + d_pitch * fb
                self.correction_series_cnt += 1

                # Магия: обнуляем таймер ожидания, чтобы выстрелить СРАЗУ
                self.fire_wait_cnt = 2  # минимальная пауза на успокоение приводов
                print(f"Промах! Попытка коррекции {self.correction_series_cnt}/{self.MAX_CORRECTION_ATTEMPTS}")
            else:
                # Попытки кончились, сбрасываемся на чистую баллистику
                self.series_stop()
                print("Серия коррекций исчерпана. Возврат к баллистике.")

        # print(f"--- SHOT REPORT ---")
        # print(f"Total: {self.shots_count} | Hits: {self.hits_count} ({self.hits_count / self.shots_count:.1%})")

    def get_nn_state(self):
        """Упаковка данных для нейросети (State)."""
        if not self.active_track:
            return np.zeros(6)

        # 1. Текущие углы на цель (отфильтрованные или прямые из трекера)
        target_yaw, target_pitch = self.active_track.last_angles

        # 2. Ошибка наведения (на сколько прицел сейчас не совпадает с целью)
        err_yaw = target_yaw - self.turret.yaw
        err_pitch = target_pitch - self.turret.pitch

        # 3. Угловая скорость (динамика цели)
        v_y, v_p = self.active_track.velocity_angles

        return np.array([
            err_yaw,
            err_pitch,
            v_y,
            v_p,
            self.active_track.filtered_dist,
            self.turret.pitch  # Наклон ствола важен для баллистики
        ], dtype=float)

    def fire(self):
        self.turret.fire()

    def set_target_by_pixel(self, x, y):
        """Первичный захват по клику мыши"""
        self.clear_target()
        best_target = None
        min_dist = 40  # Радиус поиска цели вокруг клика

        for det in self.current_detections:
            if det["type"] == "target":
                dist = np.hypot(det["pos"][0] - x, det["pos"][1] - y)
                if dist < min_dist:
                    min_dist = dist
                    best_target = det

        if best_target:
            self.handle_target_lock(best_target)
            print(f"Target locked at {self.locked_target_data['pos']}")

    def clear_target(self):
        self.locked_target_data = None
        self.is_locked = False
        self.active_track = None
        self.series_stop()

    def move_turret_to_pixel(self, x, y):
        """Сброс захвата и ручной поворот в точку"""
        self.clear_target()
        new_yaw, new_pitch = self.camera.get_angles_from_pixel(x, y)
        self.turret.set_target_angles(new_yaw, new_pitch)

    def handle_target_lock(self, detection):
        """захватить указанную цель"""
        self.locked_target_data = detection
        self.is_locked = True

        # Переводим экранные координаты в мировые
        dist = BallisticsSolver.estimate_distance(
            detection["screen_r"], self.TARGET_RADIUS, self.camera.f
        )

        if self.active_track is None:
            # Создаем новый трек
            self.active_track = TrackedTarget(
                1,
                detection["pos"][0],
                detection["pos"][1],
                dist,
                self.camera
            )
        else:
            # Обновляем существующий
            # Передаем сырые данные в трек для стабилизации
            self.active_track.update_with_screen_data(
                detection["pos"][0],
                detection["pos"][1],
                dist,
                self.camera
            )

    def _update_target_lock(self):
        """цдержание цели и донавотка турели с учктом упреждения"""
        if self.is_locked and self.locked_target_data:
            new_lock = None
            min_dist = 50  # Максимальный прыжок цели между кадрами в пикселях

            last_x, last_y = self.locked_target_data["pos"]

            for det in self.current_detections:
                if det["type"] == "target":
                    dist = np.hypot(det["pos"][0] - last_x, det["pos"][1] - last_y)
                    if dist < min_dist:
                        min_dist = dist
                        new_lock = det

            if new_lock:
                # Цель найдена, обновляем данные
                self.handle_target_lock(new_lock)

                # наводимся с учетом дистанции
                self._turret_to_target()
                self.lost_targ_cnt = 0

            else:
                self.lost_targ_cnt += 1
                if self.lost_targ_cnt > 10:
                    # Цель потеряна (ушла за экран или скрылась)
                    self.clear_target()
                    self.lost_targ_cnt = 0

    def _turret_to_target(self):
        if not self.active_track: return

        """наводимся на ту цель"""
        # Наводим турель на обновленные координаты
        target_yaw, target_pitch = self.active_track.get_fire_angles(
            np.array([0, 0, 0]),
            self.turret.projectile_speed,
            BallisticsSolver.G
        )

        if self.USE_AI:
            # 2. Получаем текущее состояние для сети
            state = self.get_nn_state()  # Возвращает [err_yaw, err_pitch, v_yaw, v_pitch, dist, t_pitch]

            # 3. Запрашиваем поправку
            d_yaw, d_pitch = self.corrector.get_correction(*state)

            # print(f"Target angles: Math({target_yaw:.3f}) | AI({d_yaw:.4f})")
            # print(f"Inputs: Dist: {state[4]:.1f} | V_yaw: {state[2]:.4f}")

            target_yaw -= d_yaw
            target_pitch -= d_pitch

        #  Поправка от "быстрого дострела" (Feedback Loop)
        target_yaw += self.feedback_offset_yaw
        target_pitch += self.feedback_offset_pitch

        self.turret.set_target_angles(target_yaw, target_pitch)


    def is_active_target(self,det_target):
        """проверим, являктся ли эта цель захваченой"""
        if self.is_locked:
            return det_target["pos"] == self.locked_target_data["pos"]
        else:
            return False

    def get_locked_distance(self):
        if self.is_locked:
            return self.locked_target_data["distance"]
        else:
            return 0.0