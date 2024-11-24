import json.decoder
import os
from typing import Literal, Type, Sequence
from pathlib import Path

from whisper import _MODELS
from pydantic import BaseModel, computed_field


whisper_models = tuple(_MODELS.keys())
WhisperModel: Type = Literal[whisper_models]


class Settings(BaseModel):
    _default_work_dir = Path(os.path.expanduser("~"), ".cache")
    ROOT_DIR: Path = Path(__file__).parent
    WORK_DIR: Path = Path(
        os.getenv("XDG_CACHE_HOME", _default_work_dir),
        "whisper"
    )
    RESTART_ERROR_CODE: int = 999
    USER_SETTINGS_PATH: Path = WORK_DIR / "settings.json"
    DEFAULT_WHISPER_MODEL: str = "small.en"
    SAMPLE_RATE: int = 44100
    BLOCK_SIZE_MSEC: int = 30
    SILENT_BLOCKS_TO_SAVE: int = 10
    VOCAL_RANGE: tuple = 50, 1000
    MIN_INPUT_DEVICE_SENSITIVITY: float = 0.0001
    MAX_INPUT_DEVICE_SENSITIVITY: float = 0.2
    MIN_TRANSCRIBE_BUFFER_LENGTH: int = 50000
    MAX_TRANSCRIBE_BUFFER_LENGTH: int = 1000000

    @computed_field
    @property
    def INPUT_DEVICE_SENSITIVITY_STEP(self) -> float:
        return (
            (
                self.MAX_INPUT_DEVICE_SENSITIVITY
                - self.MIN_INPUT_DEVICE_SENSITIVITY
            ) / 100
        )


class UserSettings(BaseModel):
    whisper_model: WhisperModel | None = None
    default_input_device: str | None = None
    input_device_sensitivity: float = 0.01
    show_input_selector_on_startup: bool = True
    print_dots_while_listening: bool = True
    translation_enabled: bool = False
    window_size: tuple = 320, 450

    @classmethod
    def load(cls, user_settings_path: Path):
        user_settings_json = {}
        if user_settings_path.exists():
            try:
                with open(user_settings_path) as file:
                    user_settings_json = json.load(file)
            except json.decoder.JSONDecodeError:
                os.unlink(user_settings_path)
        return cls(**user_settings_json)

    def save(self):
        with open(settings.USER_SETTINGS_PATH, 'w') as file:
            json.dump(self.dict(), file)


settings = Settings()
os.makedirs(settings.WORK_DIR, exist_ok=True)
user_settings = UserSettings.load(settings.USER_SETTINGS_PATH)




