"""
Stealth MCQ Helper - Main Entry Point.

Groq-powered overlay assistant for MCQ solving and text explanation.

Hotkeys (configurable via config.yaml):
  - Screenshot/MCQ: Ctrl+Alt+W (default)
  - Explain Text:   Ctrl+Alt+E (default)
  - Hide Overlay:   Delete key (default)
"""
import sys
import os
import atexit

# Set up Qt environment before importing Qt modules
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from config import get_config, CONFIG
from overlay import StealthOverlay
from controller import AppController
from tray import SystemTray
from utils import log
from logging_config import setup_logging


def main() -> None:
    """Application entry point."""
    # Initialize logging first
    setup_logging()
    
    # Qt high DPI settings
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when overlay hidden
    app.setApplicationName("4Utool")
    app.setApplicationDisplayName("updater")
    
    # Load config (validates API key)
    try:
        config = get_config()
        api_key = config.api_key
    except RuntimeError as e:
        print(f"\n{'=' * 50}")
        print(f"ERROR: {e}")
        print(f"{'=' * 50}\n")
        sys.exit(1)
    
    # Create overlay
    overlay = StealthOverlay()
    
    # Create controller
    controller = AppController(overlay, api_key)
    
    # Create system tray
    tray = SystemTray(overlay)
    tray.quit_requested.connect(app.quit)
    
    # Cleanup on exit
    def cleanup():
        controller.cleanup()
        tray.cleanup()
    
    app.aboutToQuit.connect(cleanup)
    atexit.register(cleanup)
    
    # Start listeners
    try:
        controller.start_listeners()
    except RuntimeError as e:
        print(f"\nFATAL: {e}\n")
        sys.exit(1)
    
    # Startup log
    log("=" * 50)
    log("Groq Stealth Helper RUNNING")
    log(f"1. MCQ Answer (Vision): {CONFIG.hotkeys.screenshot}")
    log(f"2. Text Explain: {CONFIG.hotkeys.explain}")
    log(f"3. Hide Overlay: {CONFIG.hotkeys.hide.capitalize()} Key")
    log(f"4. Vision Model: {CONFIG.groq.vision_model}")
    log(f"5. Text Model: {CONFIG.groq.text_model}")
    log("=" * 50)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()