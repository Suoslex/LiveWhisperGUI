from __future__ import annotations
from typing import TYPE_CHECKING
from io import BytesIO

import whisper
import numpy as np
import sounddevice as sd
import torch
from scipy.io.wavfile import write
from ffmpeg import FFmpeg

from live_whisper_gui.settings import user_settings, settings


# Created by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot
# Improved and GUI adapted by Suoslex - mtsarev06@gmail.com


if TYPE_CHECKING:
    from live_whisper_gui.gui.threads import LiveWhisperThread


class LiveWhisper:
    """
    Main class with crucial LiveWhisper functionality.
    It initializes downloaded Wisper model and enables listening
    of an input device.

    Attributes
    ----------
    _qt_thread: QtCore.QThread
        Associated thread to communicate with the GUI.
    """
    _qt_thread: LiveWhisperThread = None

    @classmethod
    def init(cls, model_path: str):
        """
        Prepares all variables for listening and loads a Whisper model to RAM.

        Parameters
        ----------
        model_path: str
            Local path to a downloaded whisper model.
        """
        cls.padding = 0
        cls.is_buffer_ready = False
        cls.buffer = np.zeros((0, 1))
        cls.ready_buffer = BytesIO()
        cls.running = False
        if hasattr(cls, 'model'):
            del cls.model
        cls.model = whisper.load_model(model_path)
        cls.running = True

    @classmethod
    def listen(
            cls,
            qt_thread: LiveWhisperThread = None,
            input_device: str = None
    ):
        """
        Starts listening of an input device and processes all incoming sounds.
        It includes preparing data and sending it to Whisper.

        Parameters
        ----------
        qt_thread: LiveWhisperThread
            Associated thread to communicate with the GUI.
        input_device: str
            Name of an input device to listen to.
        """
        if not cls.model:
            raise EnvironmentError(
                "Please use LiveWhisper.init() method "
                "before starting the listening."
            )
        cls._qt_thread = qt_thread
        with sd.InputStream(
                device=input_device,
                channels=1,
                callback=cls._callback,
                blocksize=int(
                    settings.SAMPLE_RATE * settings.BLOCK_SIZE_MSEC / 1000
                ),
                samplerate=settings.SAMPLE_RATE
        ):
            while cls.running:
                cls._process()

    @classmethod
    def _callback(cls, indata, frames, time, status):
        """
        Function used by SoundDevice to communicate with the LiveWhisper.
        """
        if not indata.any():
            return
        if len(cls.buffer) > settings.MAX_TRANSCRIBE_BUFFER_LENGTH:
            return cls._save_audio()
        freq = (
            np.argmax(np.abs(np.fft.rfft(indata[:, 0])))
            * settings.SAMPLE_RATE / frames
        )
        if (
            indata.max() > user_settings.input_device_sensitivity
            and settings.VOCAL_RANGE[0] <= freq <= settings.VOCAL_RANGE[1]
        ):
            cls._qt_thread.sendMessage('.')
            cls.buffer = np.concatenate((cls.buffer, indata))
            cls.padding = settings.SILENT_BLOCKS_TO_SAVE
        else:
            cls.padding -= 1
            if cls.padding < 1 and cls.buffer.shape[0] > settings.SAMPLE_RATE:
                cls._save_audio()

    @classmethod
    def _process(cls):
        """
        Processes prepared data by sending it to Whisper.
        """
        if cls.is_buffer_ready:
            audio = cls._load_audio()
            result = cls.model.transcribe(
                audio=audio,
                fp16=False,
                language='en' if 'en' in user_settings.whisper_model else '',
                task=(
                    'translate'
                    if user_settings.translation_enabled else
                    'transcribe'
                )
            )
            if cls._qt_thread:
                cls._qt_thread.sendMessage(result['text'])
            cls.is_buffer_ready = False

    @classmethod
    def _save_audio(cls):
        """
        Saves collected sound data and sends it to
        _process method by filling the ready_buffer.
        """
        cls.ready_buffer = BytesIO()
        write(cls.ready_buffer, settings.SAMPLE_RATE, cls.buffer)
        cls.buffer = np.zeros((0, 1))
        cls.is_buffer_ready = True

    @classmethod
    def _load_audio(cls):
        """
        Loads a collected audio from ready_buffer and prepares it
        for processing by Whisper.
        """
        ffmpeg = (
            FFmpeg()
            .option("y")
            .input("pipe:0")
            .output(
                "pipe:1",
                f="s16le",
                ac="1",
                acodec="pcm_s16le",
                ar=str(whisper.audio.SAMPLE_RATE),
            )
        )
        out = ffmpeg.execute(cls.ready_buffer)
        return torch.from_numpy(
            np.frombuffer(out, np.int16)
            .flatten()
            .astype(np.float32)
            / 32768.0
        )

