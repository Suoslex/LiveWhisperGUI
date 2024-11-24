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


class LiveWhisper:
    _qt_thread = None
    _input_device = None

    @classmethod
    def init(cls, model_path: str):
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
            qt_thread=None,
            input_device: str = None
    ):
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
    def restart_listening(cls, input_device: str = None):
        cls.listen(qt_thread=cls._qt_thread, input_device=input_device)

    @classmethod
    def _callback(cls, indata, frames, time, status):
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
            and freq in settings.VOCAL_RANGE
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
        cls.ready_buffer = BytesIO()
        write(cls.ready_buffer, settings.SAMPLE_RATE, cls.buffer)
        cls.buffer = np.zeros((0, 1))
        cls.is_buffer_ready = True

    @classmethod
    def _load_audio(cls):
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

