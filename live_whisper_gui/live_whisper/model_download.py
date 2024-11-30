from __future__ import annotations
import os
import hashlib
import warnings
import urllib
from typing import TYPE_CHECKING

from whisper import _MODELS

from live_whisper_gui.settings import settings


if TYPE_CHECKING:
    from live_whisper_gui.gui.threads import InitializationThread


def model_download(qt_thread: InitializationThread, name: str) -> str:
    """
    Downloads a Whisper model to a cache dir.

    Parameters
    ----------
    qt_thread: InitializationThread
        Associated thread to communicate with the GUI.
    name: str
        Name of a Whisper model to download.
    """
    if name not in _MODELS:
        raise EnvironmentError(f"There is no Whisper model called {name}")
    url = _MODELS[name]

    expected_sha256 = url.split("/")[-2]
    download_target = os.path.join(settings.WORK_DIR, os.path.basename(url))

    if os.path.exists(download_target) and not os.path.isfile(download_target):
        raise RuntimeError(
            f"{download_target} exists and is not a regular file"
        )

    if os.path.isfile(download_target):
        with open(download_target, "rb") as f:
            model_bytes = f.read()
        if hashlib.sha256(model_bytes).hexdigest() == expected_sha256:
            return download_target
        else:
            warnings.warn(
                f"{download_target} exists, but the SHA256 checksum "
                f"does not match; re-downloading the file"
            )

    with (
        urllib.request.urlopen(url) as source,
        open(download_target, "wb") as output
    ):
        total = int(source.info().get("Content-Length"))
        downloaded = 0
        while True:
            buffer = source.read(8192)
            if not buffer:
                break

            output.write(buffer)
            downloaded += len(buffer)
            qt_thread.sendMessage(
                f'Downloading "{name}" Whisper model...',
                downloaded,
                total
            )

    model_bytes = open(download_target, "rb").read()
    if hashlib.sha256(model_bytes).hexdigest() != expected_sha256:
        raise RuntimeError(
            "Model has been downloaded but the SHA256 checksum "
            "does not not match. Please retry loading the model."
        )

    return download_target
