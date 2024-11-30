# LiveWhisperGUI

GUI for [Nikorasu LiveWhisper script](https://github.com/Nikorasu/LiveWhisper),
a nearly-live implementation of OpenAI's Whisper using sounddevice. 
Improved and refactored, with extra features to make it much more convenient
and user-friendly.

## Features

- Window is always on top. You can use it as captions for your meetings, videos or movies.
- Double-click to copy transcribed text.
- Easily configurable. Just choose a Whisper model (or leave it to a default one), an input device, and you are good to go.
- Adjustable. Change an input device sensitivity and display settings at any time with user-friendly interface.
- Cross-platform. Use the implementation on your **Windows**, **macOS** or **Linux** device.

## Screenshots

<p float="left">
    <img src="https://github.com/Suoslex/LiveWhisperGUI/blob/main/media/preview_loading_window.png?raw=true" alt="Loading screen" height="200"/>
    <img src="https://github.com/Suoslex/LiveWhisperGUI/blob/main/media/preview_input_device_selector.png?raw=true" alt="Input device selector" height="200"/>
    <img src="https://github.com/Suoslex/LiveWhisperGUI/blob/main/media/preview_settings_window.png?raw=true" alt="Settings window" height="200"/>
</p>
<img src="https://github.com/Suoslex/LiveWhisperGUI/blob/main/media/preview_gui_1.png?raw=true" alt="GUI"/>
<img src="https://github.com/Suoslex/LiveWhisperGUI/blob/main/media/preview_gui_2.png?raw=true" alt="GUI"/>


## Dependencies 

The program requires **FFMpeg** to be installed in your system. To check if you have it,
just run the following command in your terminal:

```shell
ffmpeg -version
```

If you get any error like "**zsh: command not found: ffmpeg**", then you probably 
don't have it installed. Please refer to FFMpeg installation guide on the Internet
in this case.


## Installation using source code

1. Copy the source code to you local machine:
    ```shell
    git clone https://github.com/Suoslex/LiveWhisperGUI.git
    ```
2. Change working directory and install necessary python dependencies. 
For example, using poetry:
    ```shell
   cd LiveWhisperGUI
   poetry shell
   poetry install
    ```

3. Run the program
    ```shell
   python -m live_whisper_gui
    ```

## Sidenote

The project is in **beta**. I developed it mostly for my own research purposes,
but decided to publish to everyone in case someone finds it helpful.

I recommend to use the **small** whisper model, because it's a golden mean 
between performance and quality. You can also choose a smaller one (like tiny) 
to speed up transcribing, or a heavier one (like large) if your system is capable enough.

If you have any questions, you can contact me by my email 
([mtsarev06@gmail.com](mailto:mtsarev06@gmail.com)).
