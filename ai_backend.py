"""
AI 后端抽象层 - 支持 Claude API（在线）和 Ollama（离线）的混合模式
"""
import json
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)

# 配置文件路径
AI_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".fieldnote", "ai_config.json")


class AIProvider(Enum):
    """AI 提供者类型"""
    CLAUDE = "claude"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    AUTO = "auto"  # 优先 Claude → OpenAI Compatible → Ollama


# OpenAI 兼容提供者预设
OPENAI_PRESETS = {
    "OpenAI":           {"base_url": "https://api.openai.com/v1",                          "default_model": "gpt-4o"},
    "DeepSeek":         {"base_url": "https://api.deepseek.com/v1",                        "default_model": "deepseek-chat"},
    "通义千问 (Qwen)":   {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-plus"},
    "智谱GLM (Zhipu)":  {"base_url": "https://open.bigmodel.cn/api/paas/v4",              "default_model": "glm-4-flash"},
    "百度文心 (ERNIE)":  {"base_url": "https://qianfan.baidubce.com/v2",                   "default_model": "ernie-4.0-8k"},
    "自定义":            {"base_url": "",                                                   "default_model": ""},
}


@dataclass
class AIConfig:
    """AI 配置数据类"""
    provider: str = "auto"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_preset: str = "OpenAI"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    temperature: float = 0.3
    max_context_entries: int = 5

    @classmethod
    def load(cls) -> 'AIConfig':
        """从配置文件加载，不存在则返回默认值"""
        defaults = asdict(cls())
        try:
            if os.path.exists(AI_CONFIG_PATH):
                with open(AI_CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # merge-defaults：保留已保存的值，补充新增默认字段
                for key, val in defaults.items():
                    if key not in saved:
                        saved[key] = val
                return cls(**{k: v for k, v in saved.items() if k in defaults})
        except Exception as e:
            logger.warning("加载 AI 配置失败，使用默认值: %s", e)
        return cls()

    def save(self):
        """保存配置到文件"""
        os.makedirs(os.path.dirname(AI_CONFIG_PATH), exist_ok=True)
        with open(AI_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        logger.info("AI 配置已保存")


@dataclass
class AIResponse:
    """AI 响应数据类"""
    text: str = ""
    provider_used: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    error: str = ""
    success: bool = False


class BaseAIProvider(ABC):
    """AI 提供者抽象基类"""

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供者是否可用"""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 2048) -> AIResponse:
        """执行补全请求"""


class ClaudeProvider(BaseAIProvider):
    """Claude API 提供者"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._sdk_available = False
        try:
            import anthropic
            self._sdk_available = True
        except ImportError:
            logger.info("anthropic SDK 未安装，Claude 提供者不可用")

    def is_available(self) -> bool:
        return self._sdk_available and bool(self.api_key)

    def complete(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 2048) -> AIResponse:
        if not self.is_available():
            return AIResponse(error="Claude 不可用：缺少 API key 或 anthropic SDK", success=False)
        try:
            import anthropic
            if self._client is None:
                self._client = anthropic.Anthropic(api_key=self.api_key)
            message = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = message.content[0].text if message.content else ""
            return AIResponse(
                text=text.strip(),
                provider_used="Claude",
                tokens_input=message.usage.input_tokens,
                tokens_output=message.usage.output_tokens,
                success=True,
            )
        except Exception as e:
            logger.error("Claude API 调用失败: %s", e)
            return AIResponse(error=f"Claude API 错误: {e}", success=False)


class OllamaProvider(BaseAIProvider):
    """Ollama 本地模型提供者（零额外依赖，使用 urllib）"""

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            req = Request(f"{self.host}/api/tags", method="GET")
            with urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def complete(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 2048) -> AIResponse:
        try:
            payload = json.dumps({
                "model": self.model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }).encode("utf-8")

            req = Request(
                f"{self.host}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            text = data.get("response", "").strip()
            # Ollama 返回的 token 统计
            prompt_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)

            return AIResponse(
                text=text,
                provider_used="Ollama",
                tokens_input=prompt_tokens,
                tokens_output=output_tokens,
                success=True,
            )
        except Exception as e:
            logger.error("Ollama 调用失败: %s", e)
            return AIResponse(error=f"Ollama 错误: {e}", success=False)


class OpenAICompatibleProvider(BaseAIProvider):
    """OpenAI 兼容 API 提供者（支持 OpenAI / DeepSeek / 通义千问 / 智谱GLM / 百度文心等）"""

    def __init__(self, base_url: str, api_key: str, model: str, preset_name: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.preset_name = preset_name or "OpenAI Compatible"

    def is_available(self) -> bool:
        return bool(self.api_key) and bool(self.base_url)

    def complete(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 2048) -> AIResponse:
        if not self.is_available():
            return AIResponse(error="OpenAI 兼容提供者不可用：缺少 API key 或 Base URL", success=False)
        try:
            payload = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }).encode("utf-8")

            req = Request(
                f"{self.base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            text = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            return AIResponse(
                text=text,
                provider_used=self.preset_name,
                tokens_input=usage.get("prompt_tokens", 0),
                tokens_output=usage.get("completion_tokens", 0),
                success=True,
            )
        except Exception as e:
            logger.error("OpenAI 兼容 API 调用失败: %s", e)
            return AIResponse(error=f"{self.preset_name} API 错误: {e}", success=False)


class AIManager:
    """AI 管理器 — GUI 唯一交互入口"""

    def __init__(self):
        self.config = AIConfig.load()
        self._claude = ClaudeProvider(self.config.claude_api_key, self.config.claude_model)
        self._openai_compatible = OpenAICompatibleProvider(
            self.config.openai_base_url, self.config.openai_api_key,
            self.config.openai_model, self.config.openai_preset,
        )
        self._ollama = OllamaProvider(self.config.ollama_host, self.config.ollama_model)

    def get_provider(self) -> Optional[BaseAIProvider]:
        """根据配置返回可用的 Provider"""
        mode = self.config.provider
        if mode == AIProvider.CLAUDE.value:
            return self._claude if self._claude.is_available() else None
        elif mode == AIProvider.OPENAI_COMPATIBLE.value:
            return self._openai_compatible if self._openai_compatible.is_available() else None
        elif mode == AIProvider.OLLAMA.value:
            return self._ollama if self._ollama.is_available() else None
        else:
            # AUTO 模式：优先 Claude → OpenAI Compatible → Ollama
            if self._claude.is_available():
                return self._claude
            if self._openai_compatible.is_available():
                return self._openai_compatible
            if self._ollama.is_available():
                return self._ollama
            return None

    def complete(self, system_prompt: str, user_prompt: str) -> AIResponse:
        """获取 provider 并执行补全"""
        provider = self.get_provider()
        if provider is None:
            return AIResponse(
                error="没有可用的 AI 提供者。请在 设置 → AI设置 中配置 Claude API 密钥或启动 Ollama 服务。",
                success=False,
            )
        return provider.complete(
            system_prompt, user_prompt,
            temperature=self.config.temperature,
        )

    def get_status(self) -> dict:
        """返回各 provider 的可用状态"""
        return {
            "claude_available": self._claude.is_available(),
            "openai_available": self._openai_compatible.is_available(),
            "ollama_available": self._ollama.is_available(),
            "active_provider": self.config.provider,
        }

    def reload_config(self):
        """设置变更后重新加载"""
        self.config = AIConfig.load()
        self._claude = ClaudeProvider(self.config.claude_api_key, self.config.claude_model)
        self._openai_compatible = OpenAICompatibleProvider(
            self.config.openai_base_url, self.config.openai_api_key,
            self.config.openai_model, self.config.openai_preset,
        )
        self._ollama = OllamaProvider(self.config.ollama_host, self.config.ollama_model)
