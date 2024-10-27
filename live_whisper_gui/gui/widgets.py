from PyQt5 import QtWidgets, QtCore


class AnimatedTextEdit(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 30, 0, 0)
        self.setStyleSheet("QScrollBar:vertical { width: 5px;}")
        self.setReadOnly(True)
        self.animation = QtCore.QVariantAnimation(self)
        self.animation.valueChanged.connect(self.moveToLine)

    def append(self, text):
        old_scroll = self.verticalScrollBar().value()
        old_max_scroll = self.verticalScrollBar().maximum()
        super().append(text)
        self.verticalScrollBar().setValue(old_scroll)
        if old_max_scroll - old_scroll < 40:
            self.scrollGraduallyToBottom()

    @QtCore.pyqtSlot()
    def scrollGraduallyToBottom(self):
        self.animation.stop()
        self.animation.setStartValue(self.verticalScrollBar().value())
        self.animation.setEndValue(self.verticalScrollBar().maximum())
        self.animation.setDuration(500)
        self.animation.start()

    @QtCore.pyqtSlot(QtCore.QVariant)
    def moveToLine(self, i):
        self.verticalScrollBar().setValue(i)
