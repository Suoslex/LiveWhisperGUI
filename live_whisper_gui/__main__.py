from PyQt5 import QtWidgets

from live_whisper_gui.gui.main import InitializeWindow


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = InitializeWindow()
    ui.show()
    sys.exit(app.exec_())
