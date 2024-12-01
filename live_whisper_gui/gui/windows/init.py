import sounddevice
from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.gui.mixins import (
    MovableFramelessWindow,
    BlackDesignedWindow
)
from live_whisper_gui.gui.threads import InitializationThread
from live_whisper_gui.settings import settings, whisper_models, user_settings


class InitializeWindow(
    QtWidgets.QDialog,
    MovableFramelessWindow,
    BlackDesignedWindow
):
    """
    The first window to appear before start. It loads all necessary files and
    prepares LiveWhisper for work. Uses InitializationThread to communicate
    with the backend.

    Attributes
    ----------
    whisperModel: str
        A Whisper model to download and load in RAM.
    """
    whisperModel: str = None

    def __init__(self, *args, whisper_model: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.initGUI()
        self.whisperModel = whisper_model
        self.chosenDevice = None
        QtCore.QTimer.singleShot(10, self.afterWindowShows)

    def initGUI(self):
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
    """
    Base class for a settings window. Usually not initialized by itself.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initGUI()

    def initGUI(self):
        self.setContentsMargins(8, 8, 8, 8)
        self.setBaseSize(320, 320)

        self.chooseButton = QtWidgets.QPushButton("OK")
        self.chooseButton.clicked.connect(self.okButtonPressed)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.chooseButton)
        self.setLayout(layout)

    def okButtonPressed(self):
        self.close()


class WhisperModelSelectorWindow(SettingsWindow):
    """
    Settings window with Whisper model options to choose.
    """
    def initGUI(self):
        super().initGUI()
        self.setContentsMargins(8, 8, 8, 8)
        self.label = QtWidgets.QLabel("Choose a Whisper model")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.smallLabel = QtWidgets.QLabel(
            'If you don\'t know what to choose, leave a "small" one.'
        )
        self.smallLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.smallLabel.setStyleSheet("font-size: 9pt;")

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setStyleSheet("padding: 10px 0px;")
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


class InputDeviceSelector(SettingsWindow):
    """
    Settings window with available input devices to listen to.
    """
    chosenDevice: str = None
    availableDevices = [
        device['name'] for device in sounddevice.query_devices()
        if device['max_input_channels'] > 0
    ]

    def initGUI(self):
        super().initGUI()
        self.label = QtWidgets.QLabel("Please choose an input device:")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.addItems(self.availableDevices)
        self.listWidget.itemClicked.connect(
            lambda: self.chooseButton.setEnabled(True)
        )
        self.chooseButton.setDisabled(True)
        if user_settings.default_input_device:
            try:
                row_index = self.availableDevices.index(
                    user_settings.default_input_device
                )
            except ValueError:
                pass
            else:
                self.listWidget.setCurrentRow(row_index)
                self.chooseButton.setDisabled(False)

        self.checkbox = QtWidgets.QCheckBox("Show this window on every start")
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet('text-align:center')

        layout = self.layout()
        layout.addWidget(self.label)
        layout.addWidget(self.listWidget)
        layout.addWidget(
            self.checkbox,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.chooseButton)

    def okButtonPressed(self):
        selectedItem = self.listWidget.selectedItems().pop()
        if not selectedItem:
            return
        self.chosenDevice = selectedItem.text()
        show_input_selector_on_startup = self.checkbox.checkState() == 2
        if (
            show_input_selector_on_startup
            != user_settings.show_input_selector_on_startup
        ):
            user_settings.show_input_selector_on_startup = (
                show_input_selector_on_startup
            )
            user_settings.save()
        if self.chosenDevice != user_settings.default_input_device:
            user_settings.default_input_device = self.chosenDevice
            user_settings.save()
        self.close()
