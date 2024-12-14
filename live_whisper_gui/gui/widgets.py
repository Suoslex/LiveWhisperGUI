from PyQt5 import QtWidgets, QtCore, QtGui


class AdvancedTextEdit(QtWidgets.QTextEdit):
    """
    TextEdit which is ReadOnly and Disabled by default, but can be activated
    by double-clicking on it.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 30, 0, 0)
        self.setStyleSheet(
            "QTextEdit {border: 0px;font-size:16px;} "
            "QScrollBar:vertical {width: 5px;}"
        )
        self.setReadOnly(True)
        self.setDisabled(True)

    def event(self, e):
        if e.type() == QtCore.QEvent.MouseButtonDblClick:
            self.setDisabled(False)
        return super().event(e)

    def leaveEvent(self, a0):
        self.setDisabled(True)

