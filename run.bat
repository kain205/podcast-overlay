@echo off
ECHO Starting All Services...

REM Chạy server phiên mã trong một cửa sổ mới
start "Transcription Server" cmd /k "cd SimulStreaming-main && python simulstreaming_whisper_server.py --model_path base.en --language en --task transcribe --warmup-file ../recording.wav"

REM Đợi một vài giây để server trên khởi động
timeout /t 3

REM Chạy server gateway trong một cửa sổ mới
start "Gateway Server" cmd /k python websocket.py

REM Chạy client overlay trong một cửa sổ mới
start "Overlay Client" cmd /k python simple_overlay.py

ECHO All services launched in separate windows.