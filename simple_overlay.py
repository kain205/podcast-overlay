import sys
import time
import os
import re
from datetime import datetime
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
        self.simulator = None
        
        # Add timer to keep window topmost
        self.topmost_timer = QTimer()
        self.topmost_timer.timeout.connect(self.force_topmost)
        self.topmost_timer.start(1000)  # Check every second

    def setup_ui(self):
        # Modified window flags for game compatibility
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool  # Removed Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Text display
        self.text_label = QLabel("Waiting for text...")
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
            if self.simulator:
                self.simulator.stop()
                self.simulator.wait()
            self.topmost_timer.stop()  # Stop the timer before quitting
            QApplication.quit()
        elif event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        """Allow dragging the overlay"""
        if hasattr(self, 'drag_start_position') and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_start_position = event.globalPosition().toPoint()

class SRTReader(QThread):
    """Read and stream text from SRT files"""
    text_updated = Signal(str)
    
    def __init__(self, downloads_path="downloads"):
        super().__init__()
        self.running = True
        self.downloads_path = downloads_path
        self.current_file = None
        self.subtitles = []
        self.current_index = 0
        
    def parse_time(self, time_str):
        """Convert SRT time format to milliseconds"""
        h, m, s = time_str.split(':')
        s, ms = s.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    
    def get_srt_file(self):
        """Get the first SRT file found in downloads folder"""
        try:
            srt_files = [f for f in os.listdir(self.downloads_path) if f.endswith('.srt')]
            if srt_files:
                return os.path.join(self.downloads_path, srt_files[0])
            return None
        except Exception as e:
            print(f"Error finding SRT file: {e}")
            return None
    
    def load_srt(self, file_path):
        """Load subtitles from SRT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by double newlines to get subtitle blocks
            blocks = re.split(r'\n\s*\n', content.strip())
            subtitles = []
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # Extract timing
                    time_line = lines[1]
                    start_time, end_time = time_line.split(' --> ')
                    
                    # Extract text (everything after timing line)
                    text = ' '.join(lines[2:]).strip()
                    
                    subtitles.append({
                        'start': self.parse_time(start_time),
                        'end': self.parse_time(end_time),
                        'text': text
                    })
            
            return subtitles
        except Exception as e:
            print(f"Error parsing SRT file: {e}")
            return []
    
    def run(self):
        """Stream text from SRT file"""
        while self.running:
            # Check for SRT file
            srt_file = self.get_srt_file()
            
            if srt_file and not self.subtitles:  # Only load if we haven't loaded subtitles yet
                print(f"Loading SRT file: {srt_file}")
                self.subtitles = self.load_srt(srt_file)
                self.current_index = 0
            
            if self.subtitles:
                # Display current subtitle
                if self.current_index < len(self.subtitles):
                    self.text_updated.emit(self.subtitles[self.current_index]['text'])
                    self.current_index += 1
                else:
                    # Loop back to start
                    self.current_index = 0
            else:
                self.text_updated.emit("Waiting for SRT file in downloads folder...")
            
            time.sleep(3)  # Update every 3 seconds
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create overlay
    overlay = StreamingTextOverlay()
    overlay.show()
    
    # Start SRT reader
    reader = SRTReader()
    overlay.simulator = reader  # Keep the same attribute name for compatibility
    reader.text_updated.connect(overlay.update_text)
    reader.start()
    
    # Clean shutdown
    def cleanup():
        reader.stop()
        reader.wait()
        overlay.topmost_timer.stop()
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec())
