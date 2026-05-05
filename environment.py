from dotenv import load_dotenv
from os import getenv
from typing import cast

from ai.main import AiProviderType
from ai.deepseek import DeepSeekModelType, DeepSeekThinkingType, DeepSeekReasoningEffortType
from ui.main import UiChannelType

class Environment:
    language: str
    show_reasoning: bool
    ui_channel: UiChannelType
    ai_provider: AiProviderType
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: DeepSeekModelType | None
    deepseek_thinking: DeepSeekThinkingType | None
    deepseek_reasoning_effort: DeepSeekReasoningEffortType | None
    deepseek_max_tokens: int

    def __init__(self) -> None:
        load_dotenv()
        self.language = getenv("LANGUAGE", "")
        self.show_reasoning = getenv("SHOW_REASONING", "").lower() == "true"
        self.ui_channel = cast(UiChannelType, getenv("UI_CHANNEL", ""))
        self.ai_provider = cast(AiProviderType, getenv("AI_PROVIDER", ""))
        self.deepseek_api_key = getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url = getenv("DEEPSEEK_BASE_URL", "")
        self.deepseek_model = cast(DeepSeekModelType, getenv("DEEPSEEK_MODEL", None))
        self.deepseek_thinking = cast(DeepSeekThinkingType, getenv("DEEPSEEK_THINKING", None))
        self.deepseek_reasoning_effort = cast(DeepSeekReasoningEffortType, getenv("DEEPSEEK_REASONING_EFFORT", None))
        self.deepseek_max_tokens = int(getenv("DEEPSEEK_MAX_TOKENS", "0"))
