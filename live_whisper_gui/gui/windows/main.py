from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.gui.windows.init import (
    InitializeWindow,
    WhisperModelSelectorWindow,
    AudioDeviceSelector
)
from live_whisper_gui.gui.mixins import (
    MovableFramelessWindow,
    BlackDesignedWindow
)
from live_whisper_gui.gui.widgets import AnimatedTextEdit
from live_whisper_gui.gui.threads import (
    InitializationThread,
    LiveWhisperThread
)
from live_whisper_gui.settings import settings, whisper_models, user_settings


class MainWindow(
    QtWidgets.QMainWindow,
    MovableFramelessWindow,
    BlackDesignedWindow
):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.setBaseSize(320, 450)
        self.installEventFilter(self)

        self.textEdit = AnimatedTextEdit(self)
        self.textEdit.setPlaceholderText("Listening...")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.textEdit)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.beforeStartup()

        self.toolBarWindow = ToolbarWindow()

        QtCore.QTimer.singleShot(0, self.afterStartup)

    def beforeStartup(self):
        self.chooseWhisperModelWindow = WhisperModelSelectorWindow(self)
        if not user_settings.whisper_model:
            self.chooseWhisperModelWindow.exec()
            user_settings.whisper_model = (
                self.chooseWhisperModelWindow.chosenModel
            )
            user_settings.save()

        self.initializeWindow = InitializeWindow(
            self,
            whisper_model=user_settings.whisper_model
        )
        self.initializeWindow.exec()

        self.audioDeviceSelectorWindow = AudioDeviceSelector(self)
        if user_settings.show_input_selector_on_startup:
            self.audioDeviceSelectorWindow.exec()

    def afterStartup(self):
        self.whisperThread = LiveWhisperThread(
            self,
            inputDevice=self.audioDeviceSelectorWindow.chosenDevice
        )
        self.whisperThread.messageReceivedSignal.connect(
            self.whisperMessageReceived
        )
        self.whisperThread.finished.connect(self.whisperThreadFinished)
        self.whisperThread.start()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.HoverEnter:
            if not self._draggingMousePos:
                self.showToolbarWindow()
        if event.type() == QtCore.QEvent.HoverLeave:
            self.hideToolbarWindow()
        if obj == self and event.type() == QtCore.QEvent.Move:
            if self._draggingMousePos:
                self.toolBarWindow.hide()
        if obj == self and event.type() == QtCore.QEvent.MouseButtonRelease:
            if self._draggingMousePos:
                self.showToolbarWindow()
        return super().eventFilter(obj, event)

    def showToolbarWindow(self):
        newPos = self.geometry().topRight()
        self.toolBarWindow.move(newPos.x(), newPos.y())
        self.toolBarWindow.show()

    def hideToolbarWindow(self):
        QtCore.QTimer.singleShot(100, self.toolBarWindow.hideIfNotHovered)

    def whisperMessageReceived(self, message: str):
        self.textEdit.append(message)

    def whisperThreadFinished(self):
        del self.whisperThread


class ToolbarWindow(BlackDesignedWindow):
    _mouseInside: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_Hover)
        self.installEventFilter(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.closeButton = QtWidgets.QPushButton("x")
        self.closeButton.clicked.connect(QtWidgets.QApplication.quit)
        self.closeButton.setFixedWidth(20)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.closeButton)
        self.setLayout(layout)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.HoverEnter:
            self._mouseInside = True
        if event.type() == QtCore.QEvent.Leave:
            self._mouseInside = False
            self.hide()
        return super().eventFilter(obj, event)

    def hideIfNotHovered(self):
        if not self._mouseInside:
            self.hide()




