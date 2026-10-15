"""
Main Controller for Stealth MCQ Helper.

Orchestrates hotkeys, workers, clipboard, and the overlay.
"""
import threading
from typing import Optional

from pynput import keyboard
import pyperclip

from PyQt6.QtCore import QObject, pyqtSignal, Qt, QThread
from PyQt6.QtWidgets import QApplication

from config import CONFIG
from workers import GroqVisionWorker, GroqTextWorker
from overlay import StealthOverlay
from utils import log, log_error


class SignalBridge(QObject):
    """Bridges pynput callbacks (non-Qt threads) to Qt signals."""
    screenshot_triggered = pyqtSignal()
    text_triggered = pyqtSignal()
    escape_pressed = pyqtSignal()


class AppController(QObject):
    """
    Orchestrates hotkeys, workers, and the overlay.
    Ensures only one worker runs at a time and cleans up threads safely.
    """

    def __init__(self, overlay: StealthOverlay, api_key: str):
        super().__init__()
        self.overlay = overlay
        self.api_key = api_key
        self.active_thread: Optional[QThread] = None
        self._worker_lock = threading.Lock()
        self._shutting_down = False

        # Bridge pynput callbacks to Qt signals
        self.bridge = SignalBridge()
        self.bridge.screenshot_triggered.connect(
            self._on_screenshot_trigger, Qt.ConnectionType.QueuedConnection
        )
        self.bridge.text_triggered.connect(
            self._on_text_trigger, Qt.ConnectionType.QueuedConnection
        )
        self.bridge.escape_pressed.connect(
            self.overlay.hide_window, Qt.ConnectionType.QueuedConnection
        )

        self.hotkey_listener: Optional[keyboard.GlobalHotKeys] = None
        self.esc_listener: Optional[keyboard.Listener] = None

        # Parse hide key
        self._hide_key = self._parse_hide_key(CONFIG.hotkeys.hide)

    def _parse_hide_key(self, key_str: str):
        """Parse hide key string to pynput Key."""
        key_str = key_str.lower()
        if key_str == "delete":
            return keyboard.Key.delete
        elif key_str == "escape":
            return keyboard.Key.esc
        elif key_str == "f1":
            return keyboard.Key.f1
        elif key_str == "f2":
            return keyboard.Key.f2
        else:
            return keyboard.Key.delete

    # ---- Listener management ----

    def start_listeners(self) -> None:
        """Start global hotkey and escape key listeners."""
        log("-> Starting global hotkey listeners...")
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(
                {
                    CONFIG.hotkeys.screenshot: self._on_screenshot_hotkey,
                    CONFIG.hotkeys.explain: self._on_text_hotkey,
                }
            )
            self.hotkey_listener.start()

            self.esc_listener = keyboard.Listener(on_press=self._on_key_press)
            self.esc_listener.start()
        except (OSError, ValueError, RuntimeError) as e:
            log_error("Starting hotkey listeners", e)
            raise RuntimeError(
                "Failed to start global hotkey listeners. "
                "Ensure you have the necessary permissions."
            ) from e

    def stop_listeners(self) -> None:
        """Stop all keyboard listeners."""
        try:
            if self.hotkey_listener:
                self.hotkey_listener.stop()
            if self.esc_listener:
                self.esc_listener.stop()
        except (RuntimeError, AttributeError) as e:
            log_error("Stopping hotkey listeners", e)

    # ---- Hotkey callbacks (called from pynput thread) ----

    def _on_screenshot_hotkey(self) -> None:
        """Called when screenshot hotkey is pressed."""
        self.bridge.screenshot_triggered.emit()

    def _on_text_hotkey(self) -> None:
        """Called when text explain hotkey is pressed."""
        self.bridge.text_triggered.emit()

    def _on_key_press(self, key) -> None:
        """Called on every key press; hides overlay on configured key."""
        if key == self._hide_key:
            self.bridge.escape_pressed.emit()

    # ---- Worker management ----

    def _is_busy(self) -> bool:
        """Return True if a worker thread is currently running."""
        with self._worker_lock:
            return self.active_thread is not None and self.active_thread.isRunning()

    def _start_worker(self, worker: QThread) -> None:
        """
        Start a worker thread, ensuring the previous one is cleaned up.
        Thread-safe: blocks new workers until cleanup completes.
        """
        acquired = self._worker_lock.acquire(timeout=0.1)
        if not acquired:
            self.overlay.show_error("System busy. Please wait...")
            return

        try:
            if self._is_busy_locked():
                self.overlay.show_error("Already processing a request. Please wait...")
                return

            if self._shutting_down:
                self.overlay.show_error("Application shutting down.")
                return

            self.active_thread = worker
            worker.result_ready.connect(self.overlay.show_text)
            worker.error_occurred.connect(self.overlay.show_error)
            worker.finished_signal.connect(self._on_worker_finished)
            worker.start()
        finally:
            self._worker_lock.release()

    def _is_busy_locked(self) -> bool:
        """Return True if a worker thread is currently running. Must hold _worker_lock."""
        return self.active_thread is not None and self.active_thread.isRunning()

    def _on_worker_finished(self) -> None:
        """Called when a worker thread finishes; clean up the reference."""
        with self._worker_lock:
            if self.active_thread is not None:
                self.active_thread.wait(500)
                self.active_thread = None
            log("-> Worker finished and cleaned up.")

    # ---- Screenshot trigger ----

    def _on_screenshot_trigger(self) -> None:
        """
        Capture a screenshot on the GUI thread and send it to Groq Vision.
        """
        if self._is_busy():
            self.overlay.show_error("Already processing. Please wait...")
            return

        self.overlay.show_status("Capturing screenshot...")

        # Capture screenshot on the GUI thread (required for Qt screen APIs)
        screenshot = self._capture_screenshot()
        if screenshot is None:
            self.overlay.show_error("Screen capture failed.")
            return

        self.overlay.show_status("Sending screenshot to Groq...")
        worker = GroqVisionWorker(self.api_key, screenshot)
        self._start_worker(worker)

    def _capture_screenshot(self) -> Optional[object]:
        """Capture the full screen. Tries PIL first, then Qt fallback."""
        try:
            from PIL import ImageGrab
            return ImageGrab.grab()
        except (OSError, ImportError) as e:
            log(f"-> PIL ImageGrab failed: {e}")

        # Qt fallback (must run on GUI thread, which this is)
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                return None
            pixmap = screen.grabWindow(0)
            qimg = pixmap.toImage()
            buffer = io.BytesIO()
            qimg.save(buffer, "PNG")
            buffer.seek(0)
            from PIL import Image
            img = Image.open(buffer).convert("RGB")
            buffer.close()
            return img
        except (RuntimeError, AttributeError, OSError, IOError) as e:
            log_error("Qt screen capture fallback", e)
            return None

    # ---- Text trigger ----

    def _on_text_trigger(self) -> None:
        """
        Read manually copied text from clipboard and send it to Groq for explanation.
        User should select text, press Ctrl+C, then press Ctrl+Alt+E.
        """
        if self._is_busy():
            self.overlay.show_error("Already processing. Please wait...")
            return

        self.overlay.show_status("Reading clipboard text...")

        # Read directly from clipboard (user already pressed Ctrl+C)
        try:
            selected_text = pyperclip.paste().strip()
        except (OSError, ImportError) as e:
            log_error("Reading clipboard", e)
            selected_text = ""

        # Validate that something was copied
        if not selected_text:
            self.overlay.show_error(
                "Clipboard is empty. Pehle text select karein, Ctrl+C dabayein, phir Ctrl+Alt+E dabayein."
            )
            return

        log(f"-> Read {len(selected_text)} chars from clipboard for explanation.")
        self.overlay.show_status("Explaining text...")

        worker = GroqTextWorker(self.api_key, selected_text)
        self._start_worker(worker)

    # ---- Cleanup ----

    def cleanup(self) -> None:
        """Stop listeners and wait for any running worker to finish."""
        try:
            self._shutting_down = True
            self.stop_listeners()

            with self._worker_lock:
                if self.active_thread is not None and self.active_thread.isRunning():
                    log("-> Requesting worker cancellation...")
                    if hasattr(self.active_thread, 'cancel'):
                        self.active_thread.cancel()

                    self.active_thread.quit()
                    if not self.active_thread.wait(3000):
                        log("[WARN] Worker did not finish within 3 seconds; forcing quit.")
                        self.active_thread.terminate()
                        self.active_thread.wait(1000)
                    self.active_thread = None
        except (RuntimeError, AttributeError) as e:
            log_error("Controller cleanup", e)


# Import io at module level for _capture_screenshot
import io