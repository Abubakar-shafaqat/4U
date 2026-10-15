"""
Stealth Overlay Window for Stealth MCQ Helper.

Frameless, always-on-top, click-through overlay widget.
"""
import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QScreen, QCursor

from config import CONFIG
from utils import log, log_error


class StealthOverlay(QWidget):
    """
    A small, always-on-top, frameless overlay widget.
    Positioned on the screen containing the mouse cursor (multi-monitor aware).
    """
    def __init__(self):
        super().__init__()
        self._hwnd = None
        self._init_ui()
        self._apply_stealth_style()

    def _init_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowOpacity(CONFIG.overlay.opacity)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(
            "Ready | Ctrl+Alt+W: Answer | Ctrl+Alt+E: Explain | Delete: Hide"
        )
        self.label.setWordWrap(True)
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.setStyleSheet(
            """
            background-color: #FFFFFF;
            color: #111827;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 6px 8px;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
            """
        )
        layout.addWidget(self.label)
        self.setLayout(layout)

        self._position_overlay()
        self.hide()

    def _get_target_screen(self):
        """Get the screen containing the mouse cursor, fallback to primary."""
        try:
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            if screen is not None:
                return screen
        except (RuntimeError, AttributeError):
            pass
        # Fallback to primary screen
        return QApplication.primaryScreen()

    def _get_screen_geometry(self) -> QRect | None:
        """Get the available geometry of the target screen."""
        try:
            screen = self._get_target_screen()
            if screen is None:
                return None
            return screen.availableGeometry()
        except (RuntimeError, AttributeError):
            return None

    def _position_overlay(self) -> None:
        """Position the overlay based on config."""
        geo = self._get_screen_geometry()
        if geo is None:
            return
        
        width = CONFIG.overlay.width
        height = CONFIG.overlay.height
        margin = CONFIG.overlay.margin
        position = CONFIG.overlay.position
        
        if position == "bottom-right":
            x = geo.width() - width - margin
            y = geo.height() - height - margin
        elif position == "bottom-left":
            x = margin
            y = geo.height() - height - margin
        elif position == "top-right":
            x = geo.width() - width - margin
            y = margin
        elif position == "top-left":
            x = margin
            y = margin
        else:
            # Default to bottom-right
            x = geo.width() - width - margin
            y = geo.height() - height - margin
        
        # Ensure within screen bounds
        x = max(margin, min(x, geo.width() - width - margin))
        y = max(margin, min(y, geo.height() - height - margin))
        
        try:
            self.setGeometry(x, y, width, height)
        except (RuntimeError, AttributeError) as e:
            log_error("Overlay positioning", e)

    def _apply_stealth_style(self) -> None:
        """Apply WS_EX_NOACTIVATE on Windows to prevent focus stealing."""
        if sys.platform != "win32":
            return
        try:
            import ctypes

            self._hwnd = int(self.winId())
            if self._hwnd == 0:
                # Window not yet created; retry shortly
                QTimer.singleShot(100, self._apply_stealth_style)
                return
            current_style = ctypes.windll.user32.GetWindowLongW(
                self._hwnd, -20  # GWL_EXSTYLE
            )
            ctypes.windll.user32.SetWindowLongW(
                self._hwnd, -20, current_style | 0x08000000  # WS_EX_NOACTIVATE
            )
        except (OSError, AttributeError, RuntimeError) as e:
            log_error("Applying WS_EX_NOACTIVATE", e)

    def _show_at_position(self, text: str) -> None:
        """Common show logic."""
        try:
            self.label.setText(text)
            self._position_overlay()
            self.show()
            self.raise_()
        except (RuntimeError, AttributeError) as e:
            log_error("Overlay show", e)

    def show_text(self, text: str) -> None:
        """Display text in the overlay."""
        self._show_at_position(text)

    def show_status(self, message: str) -> None:
        """Display a status message."""
        self._show_at_position(message)

    def show_error(self, error_text: str) -> None:
        """Display an error message with a warning prefix."""
        self._show_at_position(f"⚠ {error_text}")

    def hide_window(self) -> None:
        """Hide the overlay window."""
        try:
            self.hide()
        except (RuntimeError, AttributeError) as e:
            log_error("Overlay hide_window", e)


# Import QApplication here to avoid circular import
from PyQt6.QtWidgets import QApplication