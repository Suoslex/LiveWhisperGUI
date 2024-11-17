from io import BytesIO
from typing import TYPE_CHECKING

import whisper, os
import numpy as np
import sounddevice as sd
import torch
from scipy.io.wavfile import write
from ffmpeg import FFmpeg

from live_whisper_gui.settings import user_settings

if TYPE_CHECKING:
    from live_whisper_gui.gui.threads import (
        LiveWhisperThread,
        InitializationThread
    )

# This is my attempt to make psuedo-live transcription of speech using Whisper.
# Since my system can't use pyaudio, I'm using sounddevice instead.
# This terminal implementation can run standalone or imported for assistant.py
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot

Model = 'base'     # Whisper model size (tiny, base, small, medium, large)
English = True      # Use English-only model?
Translate = False   # Translate non-English to English?
SampleRate = 44100  # Stream device recording frequency
BlockSize = 30      # Block size in milliseconds
Threshold = 0.01    # Minimum volume threshold to activate listening
Vocals = [50, 1000] # Frequency range to detect sounds that could be speech
EndBlocks = 10      # Number of blocks to wait before sending to Whisper


class LiveWhisper:
    _qt_thread = None
    _input_device = None

    @classmethod
    def init(cls, model_path: str, assist=None):
        if assist == None:  # If not being run by my assistant, just run as terminal transcriber.
            class fakeAsst(): running, talking, analyze = True, False, None
            cls.asst = fakeAsst()  # anyone know a better way to do this?
        else: cls.asst = assist
        cls.running = True
        cls.padding = 0
        cls.prevblock = cls.buffer = np.zeros((0,1))
        cls.fileready = False
        cls.ready_buffer = BytesIO()
        cls.model = whisper.load_model(model_path)

    @classmethod
    def listen(cls, qt_thread = None, input_device: str = None):
        cls._qt_thread = qt_thread
        with sd.InputStream(device=input_device, channels=1, callback=cls._callback, blocksize=int(SampleRate * BlockSize / 1000), samplerate=SampleRate):
            while cls.running and cls.asst.running: cls._process()

    @classmethod
    def _callback(cls, indata, frames, time, status):
        if not indata.any():
            return
        # Original: np.sqrt(np.mean(indata**2)) > Threshold
        # A few alternative methods exist for detecting speech.. #indata.max() > Threshold
        #zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(indata)))) / (2 * indata.shape[0]) # threshold 20
        freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * SampleRate / frames
        #print(indata.max())
        #print(freq)
        if (
            indata.max() > user_settings.input_device_sensitivity
            and Vocals[0] <= freq <= Vocals[1]
            and not cls.asst.talking
        ):
            cls._qt_thread.sendMessage('.')
            if cls.padding < 1: cls.buffer = cls.prevblock.copy()
            cls.buffer = np.concatenate((cls.buffer, indata))
            cls.padding = EndBlocks
        else:
            cls.padding -= 1
            if cls.padding > 1:
                cls.buffer = np.concatenate((cls.buffer, indata))
            elif cls.padding < 1 < cls.buffer.shape[0] > SampleRate: # if enough silence has passed, write to file.
                cls.fileready = True
                cls._save_audio()
                cls.buffer = np.zeros((0,1))
            elif cls.padding < 1 < cls.buffer.shape[0] < SampleRate: # if recording not long enough, reset buffer.
                cls.buffer = np.zeros((0,1))
                print("\033[2K\033[0G", end='', flush=True)
            else:
                cls.prevblock = indata.copy() #np.concatenate((cls.prevblock[-int(SampleRate/10):], indata)) # SLOW

    @classmethod
    def _process(cls):
        if cls.fileready:
            print("\n\033[90mTranscribing..\033[0m")
            audio = cls._load_audio()
            result = cls.model.transcribe(audio=audio,fp16=False,language='en' if English else '',task='translate' if Translate else 'transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            if cls._qt_thread:
                cls._qt_thread.sendMessage(result['text'])
            if cls.asst.analyze != None: cls.asst.analyze(result['text'])
            cls.fileready = False

    @classmethod
    def _save_audio(cls):
        cls.ready_buffer = BytesIO()
        write(cls.ready_buffer, SampleRate, cls.buffer)

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
        return torch.from_numpy(np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0)

