import sys

from PyQt5 import QtWidgets

from live_whisper_gui.settings import settings
from live_whisper_gui.gui.windows.main import MainWindow, SettingsWindow


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    while True:
        ui = MainWindow()
        ui.show()
        return_code = app.exec_()
        if return_code == settings.RESTART_ERROR_CODE:
            ui.close()
            continue
        sys.exit(return_code)
