# Simple Text Overlay

A lightweight, always-on-top text overlay that works with games and applications. Perfect for displaying subtitles, translations, or any continuous text stream.

## Features

- Always-on-top overlay window
- Works with fullscreen games
- Draggable with left mouse click
- Close with right mouse click
- Semi-transparent background
- Auto-cycling demo text
- Customizable appearance

## Requirements

```bash
pip install PySide6 pywin32
```

## Quick Start

1. Run the overlay:
```bash
python simple_overlay.py
```

2. Controls:
- Left-click and drag to move the overlay
- Right-click to close the application

## Customization

### Window Position
The overlay appears at the bottom center of your screen by default. Modify these values in `setup_ui()`:

```python
self.setGeometry(
    (screen.width() - overlay_width) // 2,  # x position
    screen.height() - overlay_height - 50,   # y position
    overlay_width,                          # width
    overlay_height                          # height
)
```

### Appearance
Customize the overlay's appearance by modifying the stylesheet in `setup_ui()`:

```python
self.text_label.setStyleSheet("""
    QLabel {
        background-color: rgba(0, 0, 0, 220);  # Background color and opacity
        color: #FFFFFF;                        # Text color
        padding: 20px;                         # Inner padding
        border-radius: 12px;                   # Rounded corners
        font-size: 20px;                       # Text size
        font-weight: bold;                     # Text weight
        border: 2px solid rgba(255, 255, 255, 80);  # Border
        font-family: 'Segoe UI', Arial, sans-serif;
    }
""")
```

### Text Update Interval
Change how frequently the demo text updates by modifying the sleep duration in `TextSimulator`:

```python
time.sleep(3)  # Update every 3 seconds
```

## Game Compatibility

The overlay uses Win32 API to maintain visibility in games:
- Works with most windowed and fullscreen games
- May be blocked by some games with anti-cheat systems
- Performance impact is minimal

## Coming Soon

- WhisperCPP integration for real-time audio transcription
- Custom text input support
- Multiple overlay instances
- Hotkey controls
