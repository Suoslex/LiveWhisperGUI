import sounddevice
from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.gui.mixins import (
    MovableFramelessWindow,
    BlackDesignedWindow
)
from live_whisper_gui.gui.threads import InitializationThread
from live_whisper_gui.settings import settings, whisper_models


class InitializeWindow(
    QtWidgets.QDialog,
    MovableFramelessWindow,
    BlackDesignedWindow
):
    whisperModel: str = None

    def __init__(self, *args, whisper_model: str, **kwargs):
        self.whisperModel = whisper_model
        super().__init__(*args, **kwargs)

        self.chosenDevice = None
        self.setFixedSize(270, 270)
        self.setContentsMargins(10, 10, 10, 10)

        self.gifLabel = QtWidgets.QLabel(self)
        self.gifLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.gifLabel.setMargin(25)
        self.gif = QtGui.QMovie(
            str(settings.ROOT_DIR / 'gui' / 'images' / 'spinner.gif')
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
        self.initializeThread = InitializationThread(self, self.whisperModel)
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

    def errorHappened(self, error: Exception):
        raise error
        self.stageLabel.setText(str(error))
        self.progressLabel.setText("-%")
        self.closeButton.show()


class SettingsWindow(
    QtWidgets.QDialog,
    MovableFramelessWindow,
    BlackDesignedWindow
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(8, 8, 8, 8)
        self.setBaseSize(320, 320)

        self.chooseButton = QtWidgets.QPushButton("OK")
        self.chooseButton.clicked.connect(self.okButtonPressed)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.chooseButton)
        self.setLayout(layout)

    def okButtonPressed(self):
        self.close()


class ChooseModelWindow(SettingsWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(8, 8, 8, 8)
        self.label = QtWidgets.QLabel("Choose a Whisper model")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.smallLabel = QtWidgets.QLabel(
            'If you don\'t know what to choose, leave a "small" one.'
        )
        self.smallLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.smallLabel.setStyleSheet("font-size: 9pt;")

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setStyleSheet("padding: 10px 0px")
        self.listWidget.addItems(whisper_models)
        self.listWidget.setCurrentRow(whisper_models.index('small.en'))

        layout = self.layout()
        layout.addWidget(self.label)
        layout.addWidget(self.smallLabel)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.chooseButton)


    def okButtonPressed(self):
        selectedItem = self.listWidget.selectedItems().pop()
        if not selectedItem:
            return
        self.chosenModel = selectedItem.text()
        self.close()


class AudioDeviceSelector(SettingsWindow):
    chosenDevice: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.label = QtWidgets.QLabel("Please choose an input device:")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        availableDevises = sounddevice.query_devices()
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setStyleSheet("padding: 10px 0px")
        self.listWidget.addItems(
            [
                device['name'] for device in availableDevises
                if device['max_input_channels'] > 0
            ]
        )

        self.chooseButton.setDisabled(True)
        self.listWidget.itemClicked.connect(
            lambda: self.chooseButton.setEnabled(True)
        )

        layout = self.layout()
        layout.addWidget(self.label)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.chooseButton)


    def okButtonPressed(self):
        selectedItem = self.listWidget.selectedItems().pop()
        if not selectedItem:
            return
        self.chosenDevice = selectedItem.text()
        self.close()
