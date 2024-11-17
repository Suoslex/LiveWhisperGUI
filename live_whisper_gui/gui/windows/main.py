import re

from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.gui.windows.init import (
    InitializeWindow,
    WhisperModelSelectorWindow,
    AudioDeviceSelector
)
from live_whisper_gui.gui.mixins import (
    FramelessWindow,
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
        widget = FramelessWindow()
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
        if obj == self and event.type() == QtCore.QEvent.Move:
            self.moveToolbarWindow()
        if event.type() == QtCore.QEvent.HoverEnter:
            if not self._draggingMousePos:
                self.showToolbarWindow()
        if event.type() == QtCore.QEvent.HoverLeave:
            self.hideToolbarWindow()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event, *args, **kwargs):
        super().resizeEvent(event, *args, **kwargs)
        self.moveToolbarWindow()

    def showToolbarWindow(self):
        self.moveToolbarWindow()
        self.toolBarWindow.stopClosing = True
        self.toolBarWindow.show()

    def moveToolbarWindow(self):
        newPos = self.geometry().topRight()
        self.toolBarWindow.move(newPos.x(), newPos.y())

    def hideToolbarWindow(self):
        self.toolBarWindow.stopClosing = False
        QtCore.QTimer.singleShot(400, self.toolBarWindow.hideIfNotHovered)

    def whisperMessageReceived(self, message: str):
        if len(message) == 1:
            self.textEdit.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            self.textEdit.insertPlainText('.')
        else:
            cursor = self.textEdit.textCursor()
            while True:
                cursor.movePosition(
                    QtGui.QTextCursor.MoveOperation.PreviousCharacter,
                    QtGui.QTextCursor.MoveMode.KeepAnchor,
                    1
                )
                last_characters = cursor.selectedText()
                if cursor.position() == 0:
                    break
                if not re.findall(r'^\.', last_characters):
                    cursor.movePosition(
                        QtGui.QTextCursor.MoveOperation.NextCharacter,
                        QtGui.QTextCursor.MoveMode.KeepAnchor,
                        1
                    )
                    break
            cursor.insertText(f"{message}\n")

    def whisperThreadFinished(self):
        del self.whisperThread


class ToolbarWindow(BlackDesignedWindow):
    stopClosing: bool = False

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
            self.stopClosing = True
        if event.type() == QtCore.QEvent.Leave:
            self.stopClosing = False
            self.hide()
        return super().eventFilter(obj, event)

    def hideIfNotHovered(self):
        if not self.stopClosing:
            self.hide()




