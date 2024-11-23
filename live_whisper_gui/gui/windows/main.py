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
from live_whisper_gui.gui.threads import LiveWhisperThread
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
        self.settingsWindow = SettingsWindow()

        mainCss = self.mainCss + "QPushButton {border: 0; font-size: 16pt}"
        self.setStyleSheet(mainCss)

        self.closeButton = QtWidgets.QPushButton("✕")
        self.closeButton.clicked.connect(QtWidgets.QApplication.quit)
        self.closeButton.setFixedWidth(20)
        self.settingsButton = QtWidgets.QPushButton("⚙")
        self.settingsButton.setFixedWidth(20)
        self.settingsButton.clicked.connect(self.settingsWindow.show)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 7)
        layout.setSpacing(5)
        layout.addWidget(self.closeButton)
        layout.addWidget(self.settingsButton)
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


class SettingsWindow(BlackDesignedWindow, MovableFramelessWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.inputLabelFont = QtGui.QFont()
        self.inputLabelFont.setPointSize(10)

        self.settingsLabel = QtWidgets.QLabel("Settings")
        self.settingsLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.whisperModelListLabel = QtWidgets.QLabel("Whisper model")
        self.whisperModelListLabel.setFont(self.inputLabelFont)
        self.whisperModelListLabel.setContentsMargins(0, 6, 0, 1)
        self.whisperModelList = QtWidgets.QComboBox()
        self.whisperModelList.addItems(whisper_models)
        self.defaultInputDeviceLabel = QtWidgets.QLabel("Default input device")
        self.defaultInputDeviceLabel.setFont(self.inputLabelFont)
        self.defaultInputDeviceLabel.setContentsMargins(0, 4, 0, 1)
        self.defaultInputDevice = QtWidgets.QComboBox()
        self.defaultInputDevice.addItems(AudioDeviceSelector.availableDevises)
        self.inputDeviceSensitivitySliderLabel = QtWidgets.QLabel(
            "Input device sensivity"
        )
        self.inputDeviceSensitivitySliderLabel.setFont(self.inputLabelFont)
        self.inputDeviceSensitivitySliderLabel.setContentsMargins(0, 4, 0, 1)
        self.inputDeviceSensitivitySlider = QtWidgets.QSlider(
            orientation=QtCore.Qt.Orientation.Horizontal
        )
        self.showInputSelectorCheckbox = QtWidgets.QCheckBox(
            "Show input selector on start"
        )
        self.showInputSelectorCheckbox.setStyleSheet(
            "margin-left:50%; margin-right:50%; margin-top: 4px; margin-bottom: 4px"
        )
        self.okButton = QtWidgets.QPushButton("OK")

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.settingsLabel)
        layout.addWidget(self.whisperModelListLabel)
        layout.addWidget(self.whisperModelList)
        layout.addWidget(self.defaultInputDeviceLabel)
        layout.addWidget(self.defaultInputDevice)
        layout.addWidget(self.inputDeviceSensitivitySliderLabel)
        layout.addWidget(self.inputDeviceSensitivitySlider)
        layout.addWidget(self.showInputSelectorCheckbox)
        layout.addWidget(self.okButton)
        self.setLayout(layout)

