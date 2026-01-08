from tur_sim.controller import Controller
from tur_sim.ui_manager import UIManager

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    controller = Controller()

    ui = UIManager(controller)
    ui.run()


