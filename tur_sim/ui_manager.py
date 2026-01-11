import pygame

from .kalman_predictor import KalmanPredictor
from .widget_buttom import WidgetButton
from .camera_base import CameraBase
from .widget_camera import WidgetCamera
from .widget_slider import WidgetSlider
from .widget_telemetry import WidgetTelemetry
from .controller import Controller

# геометтрия кнопок
BTN_W = 120
BTN_H = 40
BTN_GAP = 15

WIN_W = 1000
WIN_H = 600
WIN_GAP = 20

FPS_FONT_SIZE = 24
PAN_W = 300

SLIDER_H = 25
SLIDER_GAP = 30

TELEM_H = 120

class UIManager:
    def __init__(self, controller, width=WIN_W, height=WIN_H):

        self.controller : Controller = controller

        pygame.init()
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Robotic Turret Control System")
        try:
            self.font = pygame.font.Font(None, FPS_FONT_SIZE)
        except:
            print("Предупреждение: Не удалось загрузить стандартный шрифт PyGame.")
            self.font = None

        self.clock = pygame.time.Clock()
        self.running = True
        self.elements = []

        # Инициализация камеры и виджетов
        self.setup_ui()

        # пробуем подключить джойстик

        pygame.joystick.init()

        self.joystick = None
        self.joystick_x_val, self.joystick_y_val = 0, 0

        joystick_id = 0
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(joystick_id)
                self.joystick.init()
                self.joystick_x_val = -self.joystick.get_axis(0)
                self.joystick_y_val = -self.joystick.get_axis(1)
                print(f"[pygame] Подключен джойстик: {self.joystick.get_name()} (Осей: {self.joystick.get_numaxes()})")
            except pygame.error as e:
                print(f"[pygame] Ошибка инициализации джойстика ID {joystick_id}: {e}")
                self.joystick = None
        else:
            print("[pygame] Джойстик не найден")

    def setup_ui(self):

        # Размещаем камеру по центру-лево
        self.elements.append(WidgetCamera(
            WIN_GAP, WIN_GAP,
            self.controller))

        pan_x = self.width - PAN_W - WIN_GAP
        pan_y = WIN_GAP

        # Телеметрия справа
        self.elements.append(WidgetTelemetry(
            pan_x, pan_y, PAN_W, TELEM_H,
            self.controller))

        pan_y += TELEM_H + WIN_GAP + SLIDER_GAP

        # --- ползунки ---

        # В инициализации UI:
        self.kal_q_acc = WidgetSlider(
            x=pan_x, y=pan_y, w=PAN_W, h=SLIDER_H,
            font=self.font,
            label="Q Acceleration",
            min_val= KalmanPredictor.MIN_Q,
            max_val= KalmanPredictor.MAX_Q,
            initial_val= self.controller.get_kalman_param('q_acc'),
            action_on_release= lambda v: self.controller.set_kalman_param('q_acc',v),
            is_log=True  # Для Q маштаб очень важен
        )
        self.elements.append(self.kal_q_acc)

        pan_y += SLIDER_H + SLIDER_GAP

        self.kal_r_noise = WidgetSlider(
            x=pan_x, y=pan_y, w=PAN_W, h=SLIDER_H,
            font=self.font,
            label="R Noise",
            min_val= KalmanPredictor.MIN_R_NOISE,
            max_val= KalmanPredictor.MAX_R_NOISE,
            initial_val=self.controller.get_kalman_param('r_noise'),
            action_on_release=lambda v: self.controller.set_kalman_param('r_noise', v),
            is_log=True
        )
        self.elements.append(self.kal_r_noise)

        pan_y += SLIDER_H + SLIDER_GAP


        # --- кнопки ---
        tool_x = WIN_GAP
        tool_y = self.height - BTN_H - WIN_GAP

        # Создаем кнопкb
        self.elements.append(WidgetButton(
            tool_x,
            tool_y,
            BTN_W, BTN_H,
            self.font, "АВТОМАТ",
            lambda: self.controller.set_auto_mode(True)
        ))

        tool_x += BTN_W + BTN_GAP

        self.elements.append(WidgetButton(
            tool_x,
            tool_y,
            BTN_W, BTN_H,
            self.font, "РУЧНОЙ",
            lambda: self.controller.set_auto_mode(False)
        ))

        tool_x += BTN_W + BTN_GAP


    def run(self):
        while self.running:
            # Получаем время кадра в миллисекундах и переводим в секунды
            # tick(60) гарантирует, что цикл не выполнится быстрее 60 раз в секунду
            dt = self.clock.tick(60) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.controller.fire()

            for el in self.elements:
                el.handle_event(event)

        if self.joystick is not None:
            self._handle_joystick()

    def _handle_joystick(self):

        if self.controller.state != self.controller.STATE_MANUAL \
        or self.controller.is_locked:
            self.controller.turret.apply_joystick_control(0, 0)
            return

        pygame.event.pump()

        val_x = -self.joystick.get_axis(0)
        val_y = -self.joystick.get_axis(1)

        DEAD_ZONE = 0.05  # 5% от максимального хода стика

        if abs(val_x) < DEAD_ZONE: val_x = 0.0
        if abs(val_y) < DEAD_ZONE: val_y = 0.0

        if (self.joystick_x_val != val_x
                or self.joystick_y_val != val_y):
            self.joystick_x_val = val_x
            self.joystick_y_val = val_y

            self.controller.turret.apply_joystick_control(val_x, val_y)

    def update(self,dt):

        keys = pygame.key.get_pressed()

        # Прямое управление аоворотом турели
        dx, dy = 0, 0

        if keys[pygame.K_LEFT]:  dx = - dt
        if keys[pygame.K_RIGHT]: dx =  dt
        if keys[pygame.K_UP]:    dy = - dt
        if keys[pygame.K_DOWN]:  dy = dt

        if dx != 0 or dy != 0:
            self.controller.turret.turn(dx,dy)

        self.controller.update(dt)



    def draw(self):
        self.screen.fill((10, 10, 10))  # Темный фон
        for el in self.elements:
            el.draw(self.screen)
        pygame.display.flip()