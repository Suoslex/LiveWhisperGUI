from PyQt5 import QtCore, QtGui, QtWidgets

from live_whisper_gui.live_whisper.main import LiveWhisper
from live_whisper_gui.live_whisper.model_download import model_download


class InitializationThread(QtCore.QThread):
    """
    Thread used by GUI (InitializeWindow) and
    model_download function to communicate.

    Attributes
    ----------
    messageReceivedSignal: QtCore.pyqtSignal
        Object to send an event with new message from the function to the GUI.
    errorHappenedSignal: QtCore.pyqtSignal
        Object to senf an error event,
        when something goes wrong in the function.
    """
    messageReceivedSignal = QtCore.pyqtSignal(str, int, int)
    errorHappenedSignal = QtCore.pyqtSignal(object)

    def __init__(self, parent, modelName: str = "small"):
        """
        Parameters
        ----------
        modelName: str
            Whisper model name to download and initialize.
        """
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
        """
        Used to send a message to the GUI (InitializeWindow).

        Parameters
        ----------
        stage: str
            At which point program is running now.
        progress: int
            A number from 0 to total, representing how much work is done.
        total: int
            A number representing how much work must be done.
        """
        self.messageReceivedSignal.emit(stage, progress, total)


class LiveWhisperThread(QtCore.QThread):
    """
    Thread used by GUI (MainWindow) and
    LiveWhisper.listen() method to communicate.

    Attributes
    ----------
    messageReceivedSignal: QtCore.pyqtSignal
        Object to send an event with new message from the function to the GUI.
    errorHappenedSignal: QtCore.pyqtSignal
        Object to senf an error event,
        when something goes wrong in the function.
    """
    messageReceivedSignal = QtCore.pyqtSignal(str)
    errorHappenedSignal = QtCore.pyqtSignal(object)

    def __init__(self, parent, inputDevice: str = None):
        """
        Parameters
        ----------
        inputDevice: str
            Name of an input device to start listening to.
        """
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
        """
        Used to send a message to the GUI (MainWindow).

        Parameters
        ----------
        message: str
            Message to send to the GUI.
        """
        self.messageReceivedSignal.emit(message)
