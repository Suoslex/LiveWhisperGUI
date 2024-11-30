from PyQt5 import QtWidgets, QtCore, QtGui


class FramelessWindow(QtWidgets.QWidget):
    """
    Makes a window frameless and resizable.
    Also enables moving the window to center of the screen.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.gripSize = 12
        self.grips = []
        for i in range(4):
            grip = QtWidgets.QSizeGrip(self)
            grip.resize(self.gripSize, self.gripSize)
            self.grips.append(grip)

        QtCore.QTimer.singleShot(10, self.center)
        QtCore.QTimer.singleShot(10, self.moveGrips)

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
    """
    Makes a window movable by dragging it at any place.
    """
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
    """
    Makes a window black-styled with transparent effect.
    """

    mainCss: str = """
        QWidget {background-color: black; color: white; text-align: center;}
        QPushButton {border: 1px solid white; padding: 2px 10px;}
        QPushButton::disabled {border: 1px solid grey;}
        QComboBox {border: 1px solid white; padding: 4px}

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            right: 8px;
        }
        
        QComboBox::down-arrow {
            color: white;
            content: '-'
        }
        
        QComboBox::down-arrow:on { 
            top: 1px;
            left: 1px;
        }
        
        QComboBox QAbstractItemView {
            border: 1px solid white;
        }
        
        QSlider::handle:horizontal {
            background: white;
            border-radius: 11px; 
        }
        
        QSlider::handle:horizontal:pressed {
            background-color: lightgrey;
        }

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowOpacity(0.9)
        self.setStyleSheet(self.mainCss)
