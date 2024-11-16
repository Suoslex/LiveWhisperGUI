import os

import sounddevice
from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.gui.mixins import (
    MovableFramelessWindow,
    BlackDesignedWindow
)
from live_whisper_gui.gui.widgets import AnimatedTextEdit
from live_whisper_gui.gui.threads import (
    InitializationThread,
    LiveWhisperThread
)
from live_whisper_gui.settings import WORK_DIR, ROOT_DIR


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

        self.audioDeviceSelectorWindow = AudioDeviceSelector()
        self.audioDeviceSelectorWindow.exec()

        self.toolBarWindow = ToolbarWindow()

        QtCore.QTimer.singleShot(100, self.afterStartup)

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


class InitializeWindow(
    QtWidgets.QDialog,
    MovableFramelessWindow,
    BlackDesignedWindow
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chosenDevice = None
        self.setFixedSize(270, 270)
        self.setContentsMargins(10, 10, 10, 10)

        self.gifLabel = QtWidgets.QLabel(self)
        self.gifLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.gifLabel.setMargin(25)
        self.gif = QtGui.QMovie(
            str(ROOT_DIR / 'gui' / 'images' / 'spinner.gif')
        )
        self.gifLabel.setMovie(self.gif)
        self.gif.setScaledSize(QtCore.QSize(80, 80))
        self.gif.start()

        self.stageLabel = QtWidgets.QLabel("Initializing...")
        self.stageLabel.setWordWrap(True)
        self.stageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.progressLabel = QtWidgets.QLabel()
        self.progressLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.closeButton = QtWidgets.QPushButton("Close")
        self.closeButton.hide()
        self.closeButton.clicked.connect(QtWidgets.QApplication.quit)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.gifLabel)
        layout.addWidget(self.stageLabel)
        layout.addWidget(self.progressLabel)
        layout.addWidget(self.closeButton)
        self.setLayout(layout)
        QtCore.QTimer.singleShot(10, self.afterWindowShows)

    def afterWindowShows(self):
        os.makedirs(WORK_DIR, exist_ok=True)
        self.initializeThread = InitializationThread(self, modelName="small")
        self.initializeThread.messageReceivedSignal.connect(
            self.threadMessageReceived
        )
        self.initializeThread.errorHappenedSignal.connect(
            self.errorHappened
        )
        self.initializeThread.finished.connect(self.initializationFinished)
        self.initializeThread.start()

    def threadMessageReceived(self, stage: str, progress: int, total: int):
        self.stageLabel.setText(stage)
        self.progressLabel.setText(f"{progress*100//total}%")

    def initializationFinished(self):
        del self.initializeThread
        self.close()
        self.mainWindow = MainWindow()
        self.mainWindow.show()

    def errorHappened(self, error: Exception):
        raise error
        self.stageLabel.setText(str(error))
        self.progressLabel.setText("-%")
        self.closeButton.show()



class AudioDeviceSelector(
    QtWidgets.QDialog,
    MovableFramelessWindow,
    BlackDesignedWindow
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chosenDevice = None
        self.setBaseSize(320, 320)

        availableDevises = sounddevice.query_devices()
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setStyleSheet("padding: 10px 0px")
        self.listWidget.addItems(
            [
                device['name'] for device in availableDevises
                if device['max_input_channels'] > 0
            ]
        )

        self.label = QtWidgets.QLabel("Please choose an input device:")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.chooseButton = QtWidgets.QPushButton("OK")
        self.chooseButton.clicked.connect(self.okButtonPressed)
        self.chooseButton.setDisabled(True)
        self.listWidget.itemClicked.connect(
            lambda: self.chooseButton.setEnabled(True)
        )
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.chooseButton)
        self.setLayout(layout)

    def okButtonPressed(self):
        selectedItem = self.listWidget.selectedItems().pop()
        if not selectedItem:
            return
        self.chosenDevice = selectedItem.text()
        self.close()



