import json.decoder
import os
from typing import Literal, Type
from pathlib import Path

from whisper import _MODELS
from pydantic import BaseModel


WhisperModel: Type = Literal[tuple(_MODELS.keys())]


class Settings(BaseModel):
    _default_work_dir = Path(os.path.expanduser("~"), ".cache")
    ROOT_DIR: Path = Path(__file__).parent
    WORK_DIR: Path = Path(
        os.getenv("XDG_CACHE_HOME", _default_work_dir),
        "whisper"
    )
    USER_SETTINGS_PATH: Path = WORK_DIR / "settings.json"


class UserSettings(BaseModel):
    whisper_model: WhisperModel = "base.en"
    window_size: tuple = 300, 300
    mic_sensitivity: float = 0.01


settings = Settings()
os.makedirs(settings.WORK_DIR, exist_ok=True)
_user_settings_json = {}

if settings.USER_SETTINGS_PATH.exists():
    try:
        with open(settings.USER_SETTINGS_PATH) as file:
            _user_settings_json = json.load(file)
    except json.decoder.JSONDecodeError:
        os.unlink(settings.USER_SETTINGS_PATH)

user_settings = UserSettings(**_user_settings_json)

if not settings.USER_SETTINGS_PATH.exists():
    with open(settings.USER_SETTINGS_PATH, 'w') as file:
        json.dump(user_settings.dict(), file)


