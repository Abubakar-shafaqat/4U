"""
Worker threads for Stealth MCQ Helper.

Contains GroqVisionWorker and GroqTextWorker for background API calls.
"""
import io
import base64
import requests
from PIL import Image

from PyQt6.QtCore import QThread, pyqtSignal

from config import CONFIG
from api import _groq_endpoint, _groq_headers, _parse_groq_response, _encode_image_base64
from utils import log, log_error


class GroqVisionWorker(QThread):
    """
    Worker thread that sends a pre-captured screenshot to Groq Vision.
    The screenshot is captured on the GUI thread and passed in as a PIL Image.
    Supports cooperative cancellation via _cancelled flag.
    """
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, api_key: str, screenshot: Image.Image):
        super().__init__()
        self.api_key = api_key
        self.model = CONFIG.groq.vision_model or "llama-3.2-90b-vision-preview"
        self.screenshot = screenshot
        self._cancelled = False

    def cancel(self) -> None:
        """Request cooperative cancellation."""
        self._cancelled = True

    def run(self) -> None:
        try:
            if self._cancelled:
                return

            # Safe copy to avoid in-place mutation of GUI thread image
            img = self.screenshot.copy()
            
            # Convert RGBA/Palette to RGB before JPEG encoding
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            img.thumbnail((512, 512))
            
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=70)
            img_bytes = buffered.getvalue()
            buffered.close()

            # Base64 encoding
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")

            if self._cancelled:
                return

            prompt = CONFIG.prompts.vision

            # Groq/OpenAI format: messages array with image_url
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300,  # 500 se kam karke 300 kar diya hai
                "temperature": 0.1,
            }

            url = _groq_endpoint()
            headers = _groq_headers(self.api_key)

            log(f"-> [VisionWorker] Sending screenshot to Groq ({self.model})...")
            response = requests.post(
                url, json=payload, headers=headers, timeout=CONFIG.groq.vision_timeout
            )

            if self._cancelled:
                return

            # Agar status code 200 nahi hai, toh Groq ka exact error message print/catch karein
            if response.status_code != 200:
                try:
                    err_json = response.json()
                    err_msg = err_json.get("error", {}).get("message", response.text)
                except Exception:
                    err_msg = response.text
                raise RuntimeError(f"Groq API 400 Error: {err_msg}")

            content = _parse_groq_response(response)
            self.result_ready.emit(content)

        except RuntimeError as e:
            if not self._cancelled:
                log_error("VisionWorker Runtime error", e)
                self.error_occurred.emit(str(e))
        except requests.exceptions.Timeout:
            if not self._cancelled:
                self.error_occurred.emit("Request timed out. Check your internet connection.")
        except requests.exceptions.ConnectionError:
            if not self._cancelled:
                self.error_occurred.emit("Network error. Check your internet connection.")
        except Exception as e:
            if not self._cancelled:
                log_error("VisionWorker unexpected error", e)
                self.error_occurred.emit(f"Unexpected error: {e}")
        finally:
            self.finished_signal.emit()

class GroqTextWorker(QThread):
    """
    Worker thread that sends selected text to Groq for explanation.
    Supports cooperative cancellation via _cancelled flag.
    """
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, api_key: str, text: str):
        super().__init__()
        self.api_key = api_key
        self.model = CONFIG.groq.text_model
        self.text = text
        self._cancelled = False

    def cancel(self) -> None:
        """Request cooperative cancellation."""
        self._cancelled = True

    def run(self) -> None:
        try:
            prompt = CONFIG.prompts.text.format(text=self.text)

            # Groq/OpenAI format: messages array
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.3,
            }

            url = _groq_endpoint()
            headers = _groq_headers(self.api_key)

            log(f"-> [TextWorker] Sending text to Groq ({self.model})...")
            response = requests.post(
                url, json=payload, headers=headers, timeout=CONFIG.groq.text_timeout
            )

            if self._cancelled:
                return

            content = _parse_groq_response(response)
            self.result_ready.emit(content)

        except RuntimeError as e:
            if not self._cancelled:
                self.error_occurred.emit(str(e))
        except requests.exceptions.Timeout:
            if not self._cancelled:
                self.error_occurred.emit("Request timed out. Check your internet connection.")
        except requests.exceptions.ConnectionError:
            if not self._cancelled:
                self.error_occurred.emit("Network error. Check your internet connection.")
        except requests.exceptions.RequestException as e:
            if not self._cancelled:
                log_error("TextWorker network request", e)
                self.error_occurred.emit(f"Network error: {e}")
        except Exception as e:
            if not self._cancelled:
                log_error("TextWorker unexpected error", e)
                self.error_occurred.emit(f"Unexpected error: {e}")
        finally:
            self.finished_signal.emit()