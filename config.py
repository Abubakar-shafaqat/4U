"""
Configuration loader for Stealth MCQ Helper.

Loads from (in order of precedence):
1. config.yaml (user config)
2. Environment variables (.env)
3. Hardcoded defaults
"""
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class GroqConfig:
    vision_model: str = "llama-3.2-11b-vision-preview"
    text_model: str = "llama-3.3-70b-versatile"
    vision_timeout: int = 60
    text_timeout: int = 30


@dataclass
class HotkeysConfig:
    screenshot: str = "<ctrl>+<alt>+w"
    explain: str = "<ctrl>+<alt>+e"
    hide: str = "delete"


@dataclass
class OverlayConfig:
    width: int = 320
    height: int = 90
    opacity: float = 0.88
    position: str = "bottom-right"
    margin: int = 20


@dataclass
class ClipboardConfig:
    poll_timeout: float = 1.5
    poll_interval: float = 0.05


@dataclass
class ImageConfig:
    max_dimension: int = 1024
    jpeg_quality: int = 85


@dataclass
class PromptsConfig:
    vision: str = (
        "Aap ek stealth MCQ exam assistant hain. "
        "Is screenshot mein diye gaye MCQ sawal aur uske options (A, B, C, D) ko parhein. "
        "Sirf sahi option aur sirf 5-8 alfaz ki short Roman Urdu wajah dein.\n"
        "Format:\n"
        "Ans: Option [X]\n"
        "Reason: [Short wajah]"
    )
    text: str = (
        "Is text/sentence ko aasan Roman Urdu mein explain karo. "
        "Jawab bohot chota aur asan ho (max 15-20 words).\n\n"
        "Text: {text}"
    )


@dataclass
class LoggingConfig:
    level: str = "INFO"
    console: bool = True
    file: bool = False
    max_bytes: int = 1048576
    backup_count: int = 3


@dataclass
class AppConfig:
    groq: GroqConfig = field(default_factory=GroqConfig)
    hotkeys: HotkeysConfig = field(default_factory=HotkeysConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    clipboard: ClipboardConfig = field(default_factory=ClipboardConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Runtime: API key from env only (never from config file)
    api_key: str = field(default="", init=False)

    def __post_init__(self):
        # Load API key from environment (required)
        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not set.\n"
                "Set it in PowerShell:\n"
                '  $env:GROQ_API_KEY = "your-actual-key-here"'
            )
        if len(self.api_key) < 20:
            raise RuntimeError(
                "GROQ_API_KEY looks too short. Please verify it is correct."
            )

        # Allow GROQ_VISION_MODEL and GROQ_TEXT_MODEL env vars to override config
        env_vision_model = os.environ.get("GROQ_VISION_MODEL", "").strip()
        if env_vision_model:
            self.groq.vision_model = env_vision_model

        env_text_model = os.environ.get("GROQ_TEXT_MODEL", "").strip()
        if env_text_model:
            self.groq.text_model = env_text_model


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml_config(path: Path) -> dict:
    """Load YAML config file, return empty dict if not found."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"Invalid YAML in {path}: {e}") from e
    except OSError as e:
        raise RuntimeError(f"Cannot read {path}: {e}") from e


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load configuration from YAML file and environment.

    Args:
        config_path: Path to config.yaml. Defaults to ./config.yaml

    Returns:
        AppConfig with all settings merged and validated.
    """
    # Default config path
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    else:
        config_path = Path(config_path)

    # Load YAML
    yaml_data = _load_yaml_config(config_path)

    # Build config with defaults, then merge YAML
    defaults = AppConfig()

    # Convert defaults to dict for merging
    def dataclass_to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: dataclass_to_dict(v) for k, v in obj.__dict__.items()}
        return obj

    base_dict = dataclass_to_dict(defaults)
    merged = _deep_merge(base_dict, yaml_data)

    # Reconstruct config objects
    return AppConfig(
        groq=GroqConfig(**merged.get("groq", {})),
        hotkeys=HotkeysConfig(**merged.get("hotkeys", {})),
        overlay=OverlayConfig(**merged.get("overlay", {})),
        clipboard=ClipboardConfig(**merged.get("clipboard", {})),
        image=ImageConfig(**merged.get("image", {})),
        prompts=PromptsConfig(**merged.get("prompts", {})),
        logging=LoggingConfig(**merged.get("logging", {})),
    )


# Global config instance (lazy-loaded)
_config: Optional[AppConfig] = None


# Public CONFIG instance for direct access (lazy-loaded on first attribute access)
class _ConfigProxy:
    """Lazy proxy for CONFIG."""
    def __getattr__(self, name):
        return getattr(get_config(), name)
    def __setattr__(self, name, value):
        raise AttributeError("CONFIG is read-only")
    def __dir__(self):
        return dir(get_config())


CONFIG = _ConfigProxy()


def get_config(config_path: Optional[str] = None) -> AppConfig:
    """Get global config instance, loading on first call."""
    global _config
    if _config is None:
        _config = load_config(config_path)
    return _config


def reset_config() -> None:
    """Reset global config (for testing)."""
    global _config
    _config = None