from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.live_whisper.main import LiveWhisper
from live_whisper_gui.live_whisper.model_download import model_download


class InitializationThread(QtCore.QThread):
    messageReceivedSignal = QtCore.pyqtSignal(str, int, int)
    errorHappenedSignal = QtCore.pyqtSignal(object)

    def __init__(self, parent, modelName: str = "small"):
        super().__init__(parent=parent)
        self._modelName = modelName

    def run(self):
        try:
            model_path = model_download(qt_thread=self, name=self._modelName)
            self.sendMessage('Loading the model...', 15, 100)
            LiveWhisper.init(model_path=model_path)
            self.sendMessage('Loading the model...', 90, 100)
        except Exception as error:
            self.errorHappenedSignal.emit(error)

    def sendMessage(self, stage: str, progress: int, total: int):
        self.messageReceivedSignal.emit(stage, progress, total)


class LiveWhisperThread(QtCore.QThread):
    messageReceivedSignal = QtCore.pyqtSignal(str)
    errorHappenedSignal = QtCore.pyqtSignal(object)

    def __init__(self, parent, inputDevice: str = None):
        super().__init__(parent=parent)
        self._inputDevice = inputDevice

    def run(self):
        try:
            LiveWhisper.listen(
                qt_thread=self,
                input_device=self._inputDevice
            )
        except Exception as error:
            self.errorHappenedSignal.emit(error)

    def sendMessage(self, message: str):
        self.messageReceivedSignal.emit(message)
