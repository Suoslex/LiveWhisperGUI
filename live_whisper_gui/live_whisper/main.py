#!/usr/bin/env python3
from io import BytesIO

import whisper, os
import numpy as np
import sounddevice as sd
import torch
from scipy.io.wavfile import write
from ffmpeg import FFmpeg
from PyQt5 import QtCore

# This is my attempt to make psuedo-live transcription of speech using Whisper.
# Since my system can't use pyaudio, I'm using sounddevice instead.
# This terminal implementation can run standalone or imported for assistant.py
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot

Model = 'small'     # Whisper model size (tiny, base, small, medium, large)
English = True      # Use English-only model?
Translate = False   # Translate non-English to English?
SampleRate = 44100  # Stream device recording frequency
BlockSize = 30      # Block size in milliseconds
Threshold = 0.01    # Minimum volume threshold to activate listening
Vocals = [50, 1000] # Frequency range to detect sounds that could be speech
EndBlocks = 10      # Number of blocks to wait before sending to Whisper


class StreamHandler:
    def __init__(
            self,
            assist=None,
            qt_thread: QtCore.QThread = None,
            input_device: str = None
    ):
        if assist == None:  # If not being run by my assistant, just run as terminal transcriber.
            class fakeAsst(): running, talking, analyze = True, False, None
            self.asst = fakeAsst()  # anyone know a better way to do this?
        else: self.asst = assist
        self.qt_thread = qt_thread
        self._input_device = input_device
        self.running = True
        self.padding = 0
        self.prevblock = self.buffer = np.zeros((0,1))
        self.fileready = False
        self.ready_buffer = BytesIO()
        print("\033[96mLoading Whisper Model..\033[0m", end='', flush=True)
        self.model = whisper.load_model(f'{Model}{".en" if English else ""}')
        print("\033[90m Done.\033[0m")

    def callback(self, indata, frames, time, status):
        #if status: print(status) # for debugging, prints stream errors.
        if not indata.any():
            print('\033[31m.\033[0m', end='', flush=True) # if no input, prints red dots
            #print("\033[31mNo input or device is muted.\033[0m") #old way
            #self.running = False  # used to terminate if no input
            return
        # Original: np.sqrt(np.mean(indata**2)) > Threshold
        # A few alternative methods exist for detecting speech.. #indata.max() > Threshold
        #zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(indata)))) / (2 * indata.shape[0]) # threshold 20
        freq = np.argmax(np.abs(np.fft.rfft(indata[:, 0]))) * SampleRate / frames
        #print(indata.max())
        #print(freq)
        if indata.max() > Threshold and Vocals[0] <= freq <= Vocals[1] and not self.asst.talking:
            print('.', end='', flush=True)
            if self.padding < 1: self.buffer = self.prevblock.copy()
            self.buffer = np.concatenate((self.buffer, indata))
            self.padding = EndBlocks
        else:
            self.padding -= 1
            if self.padding > 1:
                self.buffer = np.concatenate((self.buffer, indata))
            elif self.padding < 1 < self.buffer.shape[0] > SampleRate: # if enough silence has passed, write to file.
                self.fileready = True
                self.save_audio()
                self.buffer = np.zeros((0,1))
            elif self.padding < 1 < self.buffer.shape[0] < SampleRate: # if recording not long enough, reset buffer.
                self.buffer = np.zeros((0,1))
                print("\033[2K\033[0G", end='', flush=True)
            else:
                self.prevblock = indata.copy() #np.concatenate((self.prevblock[-int(SampleRate/10):], indata)) # SLOW

    def process(self):
        if self.fileready:
            print("\n\033[90mTranscribing..\033[0m")
            audio = self.load_audio()
            result = self.model.transcribe(audio=audio,fp16=False,language='en' if English else '',task='translate' if Translate else 'transcribe')
            print(f"\033[1A\033[2K\033[0G{result['text']}")
            if self.qt_thread:
                self.qt_thread.sendMessage(result['text'])
            if self.asst.analyze != None: self.asst.analyze(result['text'])
            self.fileready = False

    def listen(self):
        print("\033[32mListening.. \033[37m(Ctrl+C to Quit)\033[0m")
        print(self._input_device)
        with sd.InputStream(device=self._input_device, channels=1, callback=self.callback, blocksize=int(SampleRate * BlockSize / 1000), samplerate=SampleRate):
            while self.running and self.asst.running: self.process()

    def save_audio(self):
        self.ready_buffer = BytesIO()
        write(self.ready_buffer, SampleRate, self.buffer)

    def load_audio(self):
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
        out = ffmpeg.execute(self.ready_buffer)
        return torch.from_numpy(np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0)


def main(qt_thread: QtCore.QThread = None, input_device: str = None):
    try:
        handler = StreamHandler(qt_thread=qt_thread, input_device=input_device)
        handler.listen()
    except (KeyboardInterrupt, SystemExit): pass
    finally:
        print("\n\033[93mQuitting..\033[0m")
        if os.path.exists('dictate.wav'): os.remove('dictate.wav')


if __name__ == '__main__':
    main()  # by Nik