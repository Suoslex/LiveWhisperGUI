import json.decoder
import os
from typing import Literal, Type
from pathlib import Path

from whisper import _MODELS
from pydantic import BaseModel


whisper_models = tuple(_MODELS.keys())
WhisperModel: Type = Literal[whisper_models]


class Settings(BaseModel):
    _default_work_dir = Path(os.path.expanduser("~"), ".cache")
    ROOT_DIR: Path = Path(__file__).parent
    WORK_DIR: Path = Path(
        os.getenv("XDG_CACHE_HOME", _default_work_dir),
        "whisper"
    )
    USER_SETTINGS_PATH: Path = WORK_DIR / "settings.json"
    DEFAULT_WHISPER_MODEL: str = "small.en"


class UserSettings(BaseModel):
    whisper_model: WhisperModel | None = None
    window_size: tuple = 300, 300
    mic_sensitivity: float = 0.01
    show_input_selector_on_startup: bool = True
    default_input_device: str | None = None

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




