"""
AI 界面组件 - 工作线程和设置对话框
"""
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal

from ai_backend import AIManager, AIConfig, AIProvider, AIResponse, OPENAI_PRESETS

logger = logging.getLogger(__name__)


class AIWorkerThread(QThread):
    """AI 异步工作线程，防止阻塞 UI"""
    finished_signal = pyqtSignal(object)  # 发射 AIResponse

    def __init__(self, ai_manager: AIManager, system_prompt: str,
                 user_prompt: str, parent=None):
        super().__init__(parent)
        self.ai_manager = ai_manager
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def run(self):
        try:
            response = self.ai_manager.complete(self.system_prompt, self.user_prompt)
        except Exception as e:
            logger.error("AI 工作线程异常: %s", e)
            response = AIResponse(error=f"AI 调用异常: {e}", success=False)
        self.finished_signal.emit(response)


class AISettingsDialog(QDialog):
    """AI 设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 设置")
        self.setMinimumWidth(500)
        self.config = AIConfig.load()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        # === 提供者选择 ===
        provider_group = QGroupBox("AI 提供者")
        provider_layout = QFormLayout()
        provider_group.setLayout(provider_layout)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "自动（Claude→OpenAI兼容→Ollama）",
            "仅 Claude",
            "仅 OpenAI兼容(含国内LLM)",
            "仅 Ollama",
        ])
        # 设置当前值
        provider_map = {
            AIProvider.AUTO.value: 0,
            AIProvider.CLAUDE.value: 1,
            AIProvider.OPENAI_COMPATIBLE.value: 2,
            AIProvider.OLLAMA.value: 3,
        }
        self.provider_combo.setCurrentIndex(provider_map.get(self.config.provider, 0))
        provider_layout.addRow("模式:", self.provider_combo)

        layout.addWidget(provider_group)

        # === Claude 设置 ===
        claude_group = QGroupBox("Claude 设置（在线）")
        claude_layout = QFormLayout()
        claude_group.setLayout(claude_layout)

        self.claude_key_input = QLineEdit()
        self.claude_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.claude_key_input.setPlaceholderText("sk-ant-...")
        self.claude_key_input.setText(self.config.claude_api_key)
        claude_layout.addRow("API 密钥:", self.claude_key_input)

        self.claude_model_combo = QComboBox()
        self.claude_model_combo.setEditable(True)
        self.claude_model_combo.addItems([
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250414",
        ])
        self.claude_model_combo.setCurrentText(self.config.claude_model)
        claude_layout.addRow("模型:", self.claude_model_combo)

        layout.addWidget(claude_group)

        # === OpenAI 兼容设置 ===
        openai_group = QGroupBox("OpenAI 兼容设置（OpenAI / DeepSeek / 通义千问 / 智谱GLM / 百度文心）")
        openai_layout = QFormLayout()
        openai_group.setLayout(openai_layout)

        self.openai_preset_combo = QComboBox()
        self.openai_preset_combo.addItems(list(OPENAI_PRESETS.keys()))
        self.openai_preset_combo.setCurrentText(self.config.openai_preset)
        self.openai_preset_combo.currentTextChanged.connect(self._on_preset_changed)
        openai_layout.addRow("预设:", self.openai_preset_combo)

        self.openai_base_url_input = QLineEdit()
        self.openai_base_url_input.setPlaceholderText("https://api.openai.com/v1")
        self.openai_base_url_input.setText(self.config.openai_base_url)
        openai_layout.addRow("API Base URL:", self.openai_base_url_input)

        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        self.openai_key_input.setText(self.config.openai_api_key)
        openai_layout.addRow("API 密钥:", self.openai_key_input)

        self.openai_model_input = QLineEdit()
        self.openai_model_input.setPlaceholderText("gpt-4o")
        self.openai_model_input.setText(self.config.openai_model)
        openai_layout.addRow("模型名称:", self.openai_model_input)

        test_openai_btn = QPushButton("测试连接")
        test_openai_btn.setMaximumWidth(120)
        test_openai_btn.clicked.connect(self._test_openai)
        openai_layout.addRow("", test_openai_btn)

        layout.addWidget(openai_group)

        # === Ollama 设置 ===
        ollama_group = QGroupBox("Ollama 设置（离线）")
        ollama_layout = QFormLayout()
        ollama_group.setLayout(ollama_layout)

        self.ollama_host_input = QLineEdit()
        self.ollama_host_input.setPlaceholderText("http://localhost:11434")
        self.ollama_host_input.setText(self.config.ollama_host)
        ollama_layout.addRow("服务地址:", self.ollama_host_input)

        self.ollama_model_input = QLineEdit()
        self.ollama_model_input.setPlaceholderText("qwen2.5:7b")
        self.ollama_model_input.setText(self.config.ollama_model)
        ollama_layout.addRow("模型名称:", self.ollama_model_input)

        test_ollama_btn = QPushButton("测试连接")
        test_ollama_btn.setMaximumWidth(120)
        test_ollama_btn.clicked.connect(self._test_ollama)
        ollama_layout.addRow("", test_ollama_btn)

        layout.addWidget(ollama_group)

        # === 隐私提示 ===
        privacy_label = QLabel(
            "注意：使用 Claude 或 OpenAI 兼容（在线模式）时，语料文本会发送到对应 API 服务器。\n"
            "如需保密，请选择「仅 Ollama」模式在本地运行。"
        )
        privacy_label.setWordWrap(True)
        privacy_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(privacy_label)

        # === 按钮 ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _on_preset_changed(self, preset_name: str):
        """预设下拉变更时自动填充 base_url 和 model"""
        preset = OPENAI_PRESETS.get(preset_name)
        if preset:
            self.openai_base_url_input.setText(preset["base_url"])
            self.openai_model_input.setText(preset["default_model"])

    def _test_openai(self):
        """测试 OpenAI 兼容 API 连接"""
        from ai_backend import OpenAICompatibleProvider
        base_url = self.openai_base_url_input.text().strip()
        api_key = self.openai_key_input.text().strip()
        model = self.openai_model_input.text().strip()
        if not base_url or not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API Base URL 和 API 密钥")
            return
        if not model:
            QMessageBox.warning(self, "提示", "请先输入模型名称")
            return
        provider = OpenAICompatibleProvider(base_url, api_key, model, self.openai_preset_combo.currentText())
        resp = provider.complete("You are a test assistant.", "Say OK.", temperature=0.1, max_tokens=10)
        if resp.success:
            QMessageBox.information(self, "连接成功",
                f"已成功连接到 {self.openai_preset_combo.currentText()}\n"
                f"模型: {model}\n回复: {resp.text}")
        else:
            QMessageBox.warning(self, "连接失败", f"API 调用失败:\n{resp.error}")

    def _test_ollama(self):
        """测试 Ollama 连接"""
        from ai_backend import OllamaProvider
        host = self.ollama_host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "提示", "请先输入 Ollama 服务地址")
            return
        provider = OllamaProvider(host, self.ollama_model_input.text().strip())
        if provider.is_available():
            QMessageBox.information(self, "连接成功", f"已成功连接到 Ollama 服务\n{host}")
        else:
            QMessageBox.warning(self, "连接失败", f"无法连接到 Ollama 服务\n{host}\n\n请确认 Ollama 已启动。")

    def get_config(self) -> AIConfig:
        """获取用户配置"""
        provider_index = self.provider_combo.currentIndex()
        provider_values = [
            AIProvider.AUTO.value, AIProvider.CLAUDE.value,
            AIProvider.OPENAI_COMPATIBLE.value, AIProvider.OLLAMA.value,
        ]

        config = AIConfig(
            provider=provider_values[provider_index],
            claude_api_key=self.claude_key_input.text().strip(),
            claude_model=self.claude_model_combo.currentText().strip(),
            openai_api_key=self.openai_key_input.text().strip(),
            openai_base_url=self.openai_base_url_input.text().strip(),
            openai_model=self.openai_model_input.text().strip(),
            openai_preset=self.openai_preset_combo.currentText(),
            ollama_host=self.ollama_host_input.text().strip(),
            ollama_model=self.ollama_model_input.text().strip(),
            temperature=self.config.temperature,
            max_context_entries=self.config.max_context_entries,
        )
        return config
