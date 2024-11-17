from PyQt5 import QtWidgets, QtCore, QtGui


class FramelessWindow(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.gripSize = 12
        self.grips = []
        for i in range(4):
            grip = QtWidgets.QSizeGrip(self)
            grip.resize(self.gripSize, self.gripSize)
            self.grips.append(grip)

        QtCore.QTimer.singleShot(0, self.center)
        QtCore.QTimer.singleShot(0, self.moveGrips)

    def center(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def moveGrips(self):
        rect = self.rect()
        self.grips[1].move(rect.right() - self.gripSize, 0)
        self.grips[2].move(
            rect.right() - self.gripSize,
            rect.bottom() - self.gripSize
        )
        self.grips[3].move(0, rect.bottom() - self.gripSize)

    def resizeEvent(self, event, *args, **kwargs):
        super().resizeEvent(event, *args, **kwargs)
        self.moveGrips()


class MovableFramelessWindow(FramelessWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._draggingMousePos = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._draggingMousePos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self._draggingMousePos is not None:
            delta = event.globalPos() - self._draggingMousePos
            self.move(self.pos() + delta)
            self._draggingMousePos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._draggingMousePos = None


class BlackDesignedWindow(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowOpacity(0.9)
        self.setStyleSheet(
            """
            QWidget {background-color: black; color: white; text-align: center;}
            QPushButton {border: 1px solid white;}
            QPushButton::disabled {border: 1px solid grey;}
            """
        )