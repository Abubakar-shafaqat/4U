"""
System Tray Icon for Stealth MCQ Helper.

Provides show/hide/quit functionality via system tray.
"""
import sys
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal, Qt

from config import CONFIG
from utils import log


class SystemTray(QObject):
    """System tray icon with menu for the overlay app."""
    
    # Signal emitted when user requests quit
    quit_requested = pyqtSignal()
    
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.tray_icon = None
        self._create_tray()
    
    def _create_tray(self) -> None:
        """Create the system tray icon and menu."""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log("System tray not available on this system")
            return
        
        self.tray_icon = QSystemTrayIcon()
        
        # Set icon (use a simple generated icon or default)
        icon = self._create_default_icon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("4Utool - Stealth MCQ Helper")
        
        # Create menu
        menu = QMenu()
        
        # Show/Hide action
        self.show_action = QAction("Show Overlay", self.tray_icon)
        self.show_action.triggered.connect(self._toggle_overlay)
        menu.addAction(self.show_action)
        
        menu.addSeparator()
        
        # Settings action (placeholder for Phase 2)
        settings_action = QAction("Settings...", self.tray_icon)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self.tray_icon)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        
        # Double-click to toggle
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Show tray icon
        self.tray_icon.show()
        log("-> System tray icon created")
    
    def _create_default_icon(self) -> QIcon:
        """Create a simple default icon."""
        # Create a simple 32x32 icon programmatically
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a simple circle with "4U" text
        painter.setBrush(QBrush(QColor("#3B82F6")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        
        painter.setPen(QColor("white"))
        painter.setFont(QApplication.font())
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "4U")
        painter.end()
        
        return QIcon(pixmap)
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_overlay()
    
    def _toggle_overlay(self) -> None:
        """Toggle overlay visibility."""
        if self.overlay.isVisible():
            self.overlay.hide_window()
            self.show_action.setText("Show Overlay")
        else:
            self.overlay.show_text("Ready | Ctrl+Alt+W: Answer | Ctrl+Alt+E: Explain | Delete: Hide")
            self.show_action.setText("Hide Overlay")
    
    def _show_settings(self) -> None:
        """Show settings dialog (placeholder)."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            None, "Settings", "Settings dialog coming in next update!"
        )
    
    def _quit(self) -> None:
        """Request application quit."""
        log("-> Quit requested from tray")
        self.quit_requested.emit()
    
    def cleanup(self) -> None:
        """Clean up tray icon."""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None