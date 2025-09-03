import sys
import time
import os
import re
import subprocess
import yt_dlp
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont
import win32gui
import win32con

class StreamingTextOverlay(QMainWindow):
    """Simple overlay that displays streaming text"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_text = ""
        self.worker = None
        
        # Add timer to keep window topmost
        self.topmost_timer = QTimer()
        self.topmost_timer.timeout.connect(self.force_topmost)
        self.topmost_timer.start(1000)  # Check every second

    def setup_ui(self):
        # Modified window flags for game compatibility
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Text display
        self.text_label = QLabel("Waiting for process to start...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        
        # Styling for overlay appearance
        self.text_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 220);
                color: #FFFFFF;
                padding: 20px;
                border-radius: 12px;
                font-size: 20px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 80);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        self.setCentralWidget(self.text_label)
        
        # Position overlay at bottom center of screen
        screen = QApplication.primaryScreen().availableGeometry()
        overlay_width = int(screen.width() * 0.6)  # 60% of screen width
        overlay_height = 120
        
        self.setGeometry(
            (screen.width() - overlay_width) // 2,
            screen.height() - overlay_height - 50,
            overlay_width,
            overlay_height
        )
        
    def update_text(self, text):
        """Update the displayed text"""
        if text != self.current_text:
            self.current_text = text
            self.text_label.setText(text if text else "...")
            
    def force_topmost(self):
        """Force window to stay on top using Win32 API"""
        hwnd = int(self.winId())
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
            
    def mousePressEvent(self, event):
        """Handle mouse clicks - right click to close, left click to drag"""
        if event.button() == Qt.RightButton:
            if self.worker:
                self.worker.stop()
                self.worker.wait()
            self.topmost_timer.stop()
            QApplication.quit()
        elif event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        """Allow dragging the overlay"""
        if hasattr(self, 'drag_start_position') and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_start_position = event.globalPosition().toPoint()

class ProcessingThread(QThread):
    """Runs the download and transcription process in the background."""
    text_updated = Signal(str)
    
    def __init__(self, url):
        super().__init__()
        self.running = True
        self.url = url
        self.proc = None

    def run(self):
        """Main processing logic."""
        if not self.running:
            return

        try:
            REPO_DIR = Path(__file__).parent
            whisper = REPO_DIR / "build/bin/Release/whisper-cli.exe"
            output_dir = REPO_DIR / "downloads"
            output_dir.mkdir(exist_ok=True)

            # 1. Download and convert audio
            self.text_updated.emit("Downloading YouTube audio...")
            print("Starting download...")
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3'
                }],
                'quiet': True, # Suppress yt-dlp console output
            }
            yt_dlp.YoutubeDL(ydl_opts).download([self.url])
            print("Download finished.")

            if not self.running: return

            # 2. Transcribe with Whisper
            audio_file = list(output_dir.glob("*.mp3"))[0]
            self.text_updated.emit("Processing with Whisper...")
            print(f"Starting transcription for {audio_file.name}...")
            
            self.proc = subprocess.Popen(
                [str(whisper), "-f", str(audio_file), "-osrt"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Redirect stderr to stdout
                text=True,
                encoding='utf-8'
            )

            # We still print whisper's output to console for debugging
            for line in self.proc.stdout:
                if not self.running:
                    break
                print(">>", line.strip())
            
            self.proc.wait()
            self.text_updated.emit("Transcription finished.")
            print("Transcription finished.")

        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.text_updated.emit(error_message)
            print(error_message)

    def stop(self):
        print("Stopping thread...")
        self.running = False
        if self.proc and self.proc.poll() is None:
            print("Terminating Whisper process...")
            self.proc.terminate()
            self.proc.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create overlay
    overlay = StreamingTextOverlay()
    overlay.show()
    
    # URL to process
    url = "https://www.youtube.com/watch?v=kKJHT6VlWro"

    # Start Processing worker
    worker = ProcessingThread(url)
    overlay.worker = worker
    # Connect the signal to the overlay's update method
    worker.text_updated.connect(overlay.update_text) 
    worker.start()
    
    # Clean shutdown
    def cleanup():
        worker.stop()
        worker.wait()
        overlay.topmost_timer.stop()
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec())
