@echo off
ECHO Cleaning up existing processes...

REM Kill any existing Python processes to free up ports
taskkill /f /im python.exe 2>nul
taskkill /f /im pythonw.exe 2>nul

REM Wait for processes to fully terminate
timeout /t 3 /nobreak >nul

ECHO Starting All Services in Windows Terminal...

start "" wt.exe --window 0 nt --title "Transcription Server" cmd /c "cd /d d:\PROJECT\podcast-overlay\SimulStreaming && python simulstreaming_whisper_server.py --model_path base.en --language en --task transcribe --warmup-file ../samples/jfk.mp3 --log-level WARNING --max_context_tokens 400 --audio_max_len 30.0" ; split-pane --horizontal --title "Gateway Server" cmd /c "cd /d d:\PROJECT\podcast-overlay && timeout /t 5 && python websocket.py" ; split-pane --vertical --title "Overlay Client" cmd /c "cd /d d:\PROJECT\podcast-overlay && python simple_overlay.py"

ECHO All services launched in a single Windows Terminal window.