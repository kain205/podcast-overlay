# Real-Time Transcription Overlay

This project captures audio from a browser tab using a Chrome extension, transcribes it in real-time with a Whisper-based backend, and displays the subtitles on a customizable, always-on-top overlay.

## Architecture

The system consists of four main components that run independently:

1.  **Audio Source (Chrome Extension)**: A browser extension that captures audio from the active tab and streams it to the Gateway Server.
2.  **Transcription Server (`simulstreaming_whisper_server.py`)**: A dedicated server running `SimulStreaming` with a whisper model. It listens on a TCP port for raw audio data and performs the transcription.
3.  **Gateway Server (`websocket.py`)**: This server acts as a bridge. It receives audio from the Chrome extension via WebSocket, uses `ffmpeg` to convert it to the correct raw audio format, and forwards it to the Transcription Server. It then receives the resulting text and broadcasts it back to the overlay client.
4.  **Overlay Client (`simple_overlay.py`)**: A PySide6 desktop application that connects to the Gateway Server as a WebSocket client. It listens for transcription text and displays it in a clean, frameless window that stays on top of other applications.

## Prerequisites

*   Python 3.10+
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

4.  **Load the Chrome Extension:**
    1.  Open Chrome and navigate to `chrome://extensions`.
    2.  Enable "Developer mode" using the toggle in the top-right corner.
    3.  Click "Load unpacked".
    4.  Select the `audio_extension` folder from this project.
    5.  The "Audio Catcher" extension should now appear in your extensions list.

## How to Run

This project includes a batch script to simplify the startup process on Windows.

1.  **Activate your virtual environment:**
    ```bash
    .\venv\Scripts\activate
    ```
2.  **Run the script:**
    Simply double-click `run.bat` or execute it from your terminal:
    ```bash
    run.bat
    ```
This will open a new Windows Terminal with three panes for the Transcription Server, Gateway Server, and Overlay Client.

### Manual Startup

If you prefer to run each component manually, open three separate terminals.

#### Step 1: Start the Transcription Server

In your **first terminal**, run the transcription server:
```bash
python SimulStreaming/simulstreaming_whisper_server.py --model_path SimulStreaming/base.en.pt --language en --task transcribe --warmup-file samples/jfk.mp3 --log-level WARNING
```

#### Step 2: Start the Gateway Server

In your **second terminal**, run the gateway server:
```bash
python websocket.py
```

#### Step 3: Start the Overlay Client

In your **third terminal**, run the overlay client:
```bash
python simple_overlay.py
```

## How to Use the Overlay

*   **Move:** Click and drag the overlay with the **left mouse button**.
*   **Close:** **Right-click** anywhere on the overlay to close the application.

### Step 4: Send Audio from Chrome

1.  Open a Chrome tab with the audio or video you want to transcribe.
2.  Click the "Audio Catcher" extension icon in your browser toolbar.
3.  Click the "Start Capture" button in the extension popup.
4.  You should see the real-time transcription appear in the overlay window.

## How to Use the Overlay

*   **Move:** Click and drag the overlay with the **left mouse button**.
*   **Close:** **Right-click** anywhere on the overlay to close the application.
