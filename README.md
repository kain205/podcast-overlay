# Real-Time Transcription Overlay

This project captures audio from a browser tab using a Chrome extension, transcribes it in real-time with a Whisper-based backend, and displays the subtitles on a customizable, always-on-top overlay.

## Architecture

The system consists of four main components that run independently:

1.  **Audio Source (Chrome Extension)**: A browser extension that captures audio from the active tab and streams it to the Gateway Server.
2.  **Transcription Server (`simulstreaming_whisper_server.py`)**: A dedicated server running `SimulStreaming` with a whisper model. It listens on a TCP port for raw audio data and performs the transcription.
3.  **Gateway Server (`websocket.py`)**: This server acts as a bridge. It receives audio from the Chrome extension via WebSocket, uses `ffmpeg` to convert it to the correct raw audio format, and forwards it to the Transcription Server. It then receives the resulting text and broadcasts it back to the overlay client.
4.  **Overlay Client (`simple_overlay.py`)**: A PySide6 desktop application that connects to the Gateway Server as a WebSocket client. It listens for transcription text and displays it in a clean, frameless window that stays on top of other applications.

## Prerequisites

*   Python 3.8+
*   `ffmpeg` installed and available in your system's PATH.
*   A C++ compiler and build tools for dependencies.
*   Google Chrome or a Chromium-based browser.

## Setup & Installation

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    *(Note: You will need to create a `requirements.txt` file containing `websockets`, `pyside6`, `pywin32`, `whisper-streaming`, etc.)*

4.  **Load the Chrome Extension:**
    1.  Open Chrome and navigate to `chrome://extensions`.
    2.  Enable "Developer mode" using the toggle in the top-right corner.
    3.  Click "Load unpacked".
    4.  Select the `new_extension` folder from this project.
    5.  The "Audio Catcher" extension should now appear in your extensions list.

## How to Reproduce Step-by-Step

You will need to open **three separate terminal windows** and your Chrome browser.

### Step 1: Start the Transcription Server

In your **first terminal**, navigate to the `SimulStreaming-main` directory and run the `simulstreaming_whisper_server.py`. This server will perform the transcription.

```bash
cd SimulStreaming-main
python simulstreaming_whisper_server.py --model_path base.en --language en --task transcribe --warmup-file ../recording.wav
```

Keep this terminal running.

### Step 2: Start the Gateway Server

In your **second terminal**, run the `websocket.py` script from the project root. This server listens for audio from the Chrome extension.

```bash
python websocket.py
```

This will start listening on `ws://localhost:8765`. Keep this terminal running.

### Step 3: Start the Overlay Client

In your **third terminal**, run the `simple_overlay.py` script from the project root. This will open the transparent overlay window.

```bash
python simple_overlay.py
```

The overlay will appear on your screen.

### Step 4: Send Audio from Chrome

1.  Open a Chrome tab with the audio or video you want to transcribe.
2.  Click the "Audio Catcher" extension icon in your browser toolbar.
3.  Click the "Start Capture" button in the extension popup.
4.  You should see the real-time transcription appear in the overlay window.

## How to Use the Overlay

*   **Move:** Click and drag the overlay with the **left mouse button**.
*   **Close:** **Right-click** anywhere on the overlay to close the application.
