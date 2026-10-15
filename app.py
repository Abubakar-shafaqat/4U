"""
Stealth MCQ Helper - Legacy Compatibility Module.

This module provides backward compatibility for code that imports from 'app'.
New code should import directly from the respective modules:
- api: _parse_groq_response, _groq_endpoint, _groq_headers
- workers: GroqVisionWorker, GroqTextWorker
- overlay: StealthOverlay
- controller: AppController
- config: get_config, CONFIG, load_config
- utils: log, log_error
- settings: show_settings_dialog
- tray: SystemTray
- main: main
"""

# Re-export public API for backward compatibility
from api import _parse_groq_response, _groq_endpoint, _groq_headers
from workers import GroqVisionWorker, GroqTextWorker
from overlay import StealthOverlay
from controller import AppController
from config import get_config, CONFIG, load_config, reset_config
from utils import log, log_error
from settings import show_settings_dialog
from tray import SystemTray

# Constants (for backward compatibility)
GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_VISION_MODEL = CONFIG.groq.vision_model
GROQ_TEXT_MODEL = CONFIG.groq.text_model
SCREENSHOT_HOTKEY = CONFIG.hotkeys.screenshot
TEXT_HOTKEY = CONFIG.hotkeys.explain
HIDE_KEY = None  # Use controller._parse_hide_key(CONFIG.hotkeys.hide)

WS_EX_NOACTIVATE = 0x08000000
GWL_EXSTYLE = -20

# Main entry point
from main import main

__all__ = [
    '_parse_groq_response',
    '_groq_endpoint',
    '_groq_headers',
    'GroqVisionWorker',
    'GroqTextWorker',
    'StealthOverlay',
    'AppController',
    'get_config',
    'CONFIG',
    'load_config',
    'reset_config',
    'log',
    'log_error',
    'show_settings_dialog',
    'SystemTray',
    'main',
    'GROQ_API_BASE',
    'GROQ_VISION_MODEL',
    'GROQ_TEXT_MODEL',
    'SCREENSHOT_HOTKEY',
    'TEXT_HOTKEY',
    'HIDE_KEY',
    'WS_EX_NOACTIVATE',
    'GWL_EXSTYLE',
]