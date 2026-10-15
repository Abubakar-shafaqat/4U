"""
Settings Dialog for Stealth MCQ Helper.

Allows users to configure hotkeys, model, overlay appearance, etc.
"""
import yaml
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QPushButton, QDialogButtonBox,
    QTabWidget, QWidget, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt

from config import CONFIG, load_config, reset_config
from app import log


class SettingsDialog(QDialog):
    """Settings dialog for the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("4Utool Settings")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._config_path = Path(__file__).parent / "config.yaml"
        self._original_config = None
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Hotkeys tab
        hotkeys_tab = self._create_hotkeys_tab()
        tabs.addTab(hotkeys_tab, "Hotkeys")
        
        # Overlay tab
        overlay_tab = self._create_overlay_tab()
        tabs.addTab(overlay_tab, "Overlay")
        
        # Prompts tab
        prompts_tab = self._create_prompts_tab()
        tabs.addTab(prompts_tab, "Prompts")
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Vision Model
        self.vision_model_combo = QComboBox()
        self.vision_model_combo.addItems([
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview",
        ])
        self.vision_model_combo.setEditable(True)
        layout.addRow("Vision Model:", self.vision_model_combo)
        
        # Text Model
        self.text_model_combo = QComboBox()
        self.text_model_combo.addItems([
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ])
        self.text_model_combo.setEditable(True)
        layout.addRow("Text Model:", self.text_model_combo)
        
        # Vision timeout
        self.vision_timeout = QSpinBox()
        self.vision_timeout.setRange(10, 300)
        self.vision_timeout.setSuffix(" seconds")
        layout.addRow("Vision Timeout:", self.vision_timeout)
        
        # Text timeout
        self.text_timeout = QSpinBox()
        self.text_timeout.setRange(5, 120)
        self.text_timeout.setSuffix(" seconds")
        layout.addRow("Text Timeout:", self.text_timeout)
        
        return tab
    
    def _create_hotkeys_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Screenshot hotkey
        self.screenshot_hotkey = QLineEdit()
        self.screenshot_hotkey.setPlaceholderText("e.g. <ctrl>+<alt>+w")
        layout.addRow("Screenshot (MCQ):", self.screenshot_hotkey)
        
        # Explain hotkey
        self.explain_hotkey = QLineEdit()
        self.explain_hotkey.setPlaceholderText("e.g. <ctrl>+<alt>+e")
        layout.addRow("Explain Text:", self.explain_hotkey)
        
        # Hide key
        self.hide_key = QComboBox()
        self.hide_key.addItems(["Delete", "Escape", "F1", "F2"])
        layout.addRow("Hide Overlay:", self.hide_key)
        
        # Note
        note = QLabel("Note: Hotkey changes require app restart.")
        note.setStyleSheet("color: #6B7280; font-size: 11px;")
        note.setWordWrap(True)
        layout.addRow("", note)
        
        return tab
    
    def _create_overlay_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Width
        self.overlay_width = QSpinBox()
        self.overlay_width.setRange(200, 800)
        self.overlay_width.setSuffix(" px")
        layout.addRow("Width:", self.overlay_width)
        
        # Height
        self.overlay_height = QSpinBox()
        self.overlay_height.setRange(60, 400)
        self.overlay_height.setSuffix(" px")
        layout.addRow("Height:", self.overlay_height)
        
        # Opacity
        self.overlay_opacity = QDoubleSpinBox()
        self.overlay_opacity.setRange(0.3, 1.0)
        self.overlay_opacity.setSingleStep(0.05)
        self.overlay_opacity.setDecimals(2)
        layout.addRow("Opacity:", self.overlay_opacity)
        
        # Position
        self.overlay_position = QComboBox()
        self.overlay_position.addItems([
            "Bottom Right",
            "Bottom Left",
            "Top Right",
            "Top Left",
        ])
        layout.addRow("Position:", self.overlay_position)
        
        # Margin
        self.overlay_margin = QSpinBox()
        self.overlay_margin.setRange(0, 100)
        self.overlay_margin.setSuffix(" px")
        layout.addRow("Margin:", self.overlay_margin)
        
        return tab
    
    def _create_prompts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Vision prompt
        vision_group = QGroupBox("Vision Prompt (MCQ Solver)")
        vision_layout = QVBoxLayout(vision_group)
        self.vision_prompt = QTextEdit()
        self.vision_prompt.setPlaceholderText("Enter vision prompt...")
        self.vision_prompt.setMinimumHeight(150)
        vision_layout.addWidget(self.vision_prompt)
        layout.addWidget(vision_group)
        
        # Text prompt
        text_group = QGroupBox("Text Prompt (Explanation)")
        text_layout = QVBoxLayout(text_group)
        self.text_prompt = QTextEdit()
        self.text_prompt.setPlaceholderText("Enter text prompt (use {text} placeholder)...")
        self.text_prompt.setMinimumHeight(150)
        text_layout.addWidget(self.text_prompt)
        layout.addWidget(text_group)
        
        return tab
    
    def _load_current_settings(self) -> None:
        """Load current settings into UI."""
        # General
        self.vision_model_combo.setCurrentText(CONFIG.groq.vision_model)
        self.text_model_combo.setCurrentText(CONFIG.groq.text_model)
        self.vision_timeout.setValue(CONFIG.groq.vision_timeout)
        self.text_timeout.setValue(CONFIG.groq.text_timeout)
        
        # Hotkeys
        self.screenshot_hotkey.setText(CONFIG.hotkeys.screenshot)
        self.explain_hotkey.setText(CONFIG.hotkeys.explain)
        self.hide_key.setCurrentText(CONFIG.hotkeys.hide.capitalize())
        
        # Overlay
        self.overlay_width.setValue(CONFIG.overlay.width)
        self.overlay_height.setValue(CONFIG.overlay.height)
        self.overlay_opacity.setValue(CONFIG.overlay.opacity)
        self.overlay_position.setCurrentText(
            CONFIG.overlay.position.replace("-", " ").title()
        )
        self.overlay_margin.setValue(CONFIG.overlay.margin)
        
        # Prompts
        self.vision_prompt.setPlainText(CONFIG.prompts.vision)
        self.text_prompt.setPlainText(CONFIG.prompts.text)
    
    def _apply_settings(self) -> None:
        """Apply settings to config file."""
        try:
            # Load existing YAML to preserve structure/comments
            yaml_data = {}
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f) or {}
            
            # Update with new values
            yaml_data.setdefault('groq', {})['vision_model'] = self.vision_model_combo.currentText().strip()
            yaml_data['groq']['text_model'] = self.text_model_combo.currentText().strip()
            yaml_data['groq']['vision_timeout'] = self.vision_timeout.value()
            yaml_data['groq']['text_timeout'] = self.text_timeout.value()
            
            yaml_data.setdefault('hotkeys', {})['screenshot'] = self.screenshot_hotkey.text().strip()
            yaml_data['hotkeys']['explain'] = self.explain_hotkey.text().strip()
            yaml_data['hotkeys']['hide'] = self.hide_key.currentText().lower()
            
            yaml_data.setdefault('overlay', {})['width'] = self.overlay_width.value()
            yaml_data['overlay']['height'] = self.overlay_height.value()
            yaml_data['overlay']['opacity'] = self.overlay_opacity.value()
            yaml_data['overlay']['position'] = self.overlay_position.currentText().lower().replace(" ", "-")
            yaml_data['overlay']['margin'] = self.overlay_margin.value()
            
            yaml_data.setdefault('prompts', {})['vision'] = self.vision_prompt.toPlainText()
            yaml_data['prompts']['text'] = self.text_prompt.toPlainText()
            
            # Write back
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            log("-> Settings saved to config.yaml")
            
            # Reload config
            reset_config()
            from config import get_config
            get_config()
            
            QMessageBox.information(
                self, "Settings Saved",
                "Settings saved successfully!\n\n"
                "Note: Hotkey changes require an app restart to take effect."
            )
            
        except Exception as e:
            log(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")
    
    def _on_accept(self) -> None:
        """Handle OK button."""
        self._apply_settings()
        self.accept()


def show_settings_dialog(parent=None) -> None:
    """Show the settings dialog."""
    dialog = SettingsDialog(parent)
    dialog.exec()