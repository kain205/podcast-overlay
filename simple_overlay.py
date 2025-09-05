# simple_overlay_realtime.py
import sys
import time
import asyncio  # Thêm vào
import websockets # Thêm vào
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont
import win32gui
import win32con

# Lớp StreamingTextOverlay giữ nguyên, không cần thay đổi
class StreamingTextOverlay(QMainWindow):
    """Simple overlay that displays streaming text"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_text = ""
        self.worker = None
        
        self.topmost_timer = QTimer()
        self.topmost_timer.timeout.connect(self.force_topmost)
        self.topmost_timer.start(1000)

    def setup_ui(self):
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.text_label = QLabel("Connecting to server...") # Thay đổi text ban đầu
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        
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
        
        screen = QApplication.primaryScreen().availableGeometry()
        overlay_width = int(screen.width() * 0.6)
        overlay_height = 120
        
        self.setGeometry(
            (screen.width() - overlay_width) // 2,
            screen.height() - overlay_height - 50,
            overlay_width,
            overlay_height
        )
        
    def update_text(self, text):
        if text != self.current_text:
            self.current_text = text
            self.text_label.setText(text if text else "...")
            
    def force_topmost(self):
        hwnd = int(self.winId())
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
            
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.worker:
                self.worker.stop()
            self.topmost_timer.stop()
            QApplication.quit()
        elif event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_start_position') and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_start_position = event.globalPosition().toPoint()

# --- PHẦN PHẪU THUẬT CHÍNH ---
class WebSocketClientThread(QThread):
    """Runs the WebSocket client in the background to listen for transcriptions."""
    text_updated = Signal(str)
    
    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        self.running = True
        self.loop = None
        self.task = None

    async def connect_and_listen(self):
        """The core asyncio logic for connecting and listening."""
        while self.running:
            try:
                # Kết nối đến server
                async with websockets.connect(self.uri) as websocket:
                    self.text_updated.emit("Connected. Waiting for audio...")
                    print("Connected to WebSocket server.")
                    # Vòng lặp lắng nghe tin nhắn
                    async for message in websocket:
                        if not self.running:
                            break
                        self.text_updated.emit(message)
            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
                error_message = f"Connection lost: {e}. Retrying in 5s..."
                self.text_updated.emit(error_message)
                print(error_message)
                await asyncio.sleep(5)
            except Exception as e:
                error_message = f"An error occurred: {e}"
                self.text_updated.emit(error_message)
                print(error_message)
                break

    def run(self):
        """Main thread entry point. Sets up and runs the asyncio event loop."""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.task = self.loop.create_task(self.connect_and_listen())
            self.loop.run_until_complete(self.task)
        except asyncio.CancelledError:
            # Task was cancelled, this is expected on shutdown
            pass
        finally:
            self.loop.close()

    def stop(self):
        print("Stopping WebSocket client thread...")
        self.running = False
        if self.task:
            self.task.cancel()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = StreamingTextOverlay()
    overlay.show()
    
    server_uri = "ws://localhost:8765"

    # Khởi tạo và chạy worker mới
    worker = WebSocketClientThread(server_uri)
    overlay.worker = worker
    worker.text_updated.connect(overlay.update_text) 
    worker.start()
    
    # Clean shutdown
    def cleanup():
        worker.stop()
        worker.wait() # Chờ thread kết thúc hẳn
        overlay.topmost_timer.stop()
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec())