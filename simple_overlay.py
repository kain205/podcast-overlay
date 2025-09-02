import sys
import time
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

class TextSimulator(QThread):
    """Simulate streaming text for demonstration"""
    text_updated = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.demo_texts = [
            "Welcome to the text overlay system!",
            "This overlay can display continuous text streams...",
            "Perfect for subtitles, transcriptions, or live captions.",
            "You can drag it around with left click.",
            "Right click to close the overlay.",
            "This is ideal for podcast transcriptions!",
            "The text updates smoothly and stays on top.",
            "Customize the appearance as needed.",
        ]
        
    def run(self):
        """Simulate text streaming"""
        index = 0
        while self.running:
            if index < len(self.demo_texts):
                self.text_updated.emit(self.demo_texts[index])
                index += 1
            else:
                index = 0  # Loop back to start
            
            time.sleep(3)  # Update every 3 seconds
            
    def stop(self):
        self.running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create overlay
    overlay = StreamingTextOverlay()
    overlay.show()
    
    # Start text simulation
    simulator = TextSimulator()
    overlay.simulator = simulator
    simulator.text_updated.connect(overlay.update_text)
    simulator.start()
    
    # Clean shutdown
    def cleanup():
        simulator.stop()
        simulator.wait()
        overlay.topmost_timer.stop()
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec())
