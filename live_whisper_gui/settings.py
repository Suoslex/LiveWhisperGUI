import os
from pathlib import Path

_default_work_dir = Path(os.path.expanduser("~"), ".cache")
ROOT_DIR = Path(__file__).parent
WORK_DIR = Path(
    os.getenv("XDG_CACHE_HOME", _default_work_dir),
    "whisper"
)
