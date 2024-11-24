from PyQt5 import QtWidgets, QtCore, QtGui


class AdvancedTextEdit(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 30, 0, 0)
        self.setStyleSheet("QScrollBar:vertical { width: 5px;}")
        self.setReadOnly(True)

    def event(self, e):
        if e.type() == QtCore.QEvent.MouseButtonDblClick:
            self.setDisabled(False)
        return super().event(e)

    def leaveEvent(self, a0):
        self.setDisabled(True)

