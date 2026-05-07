from dotenv import load_dotenv
from os import getenv


class Environment:
    language: str
    show_reasoning: bool
    ui_channel: str
    ai_provider: str
    db_path: str
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    deepseek_thinking: str
    deepseek_reasoning_effort: str
    deepseek_max_tokens: int

    def __init__(self) -> None:
        load_dotenv()
        self.language = getenv("LANGUAGE", "")
        self.show_reasoning = getenv("SHOW_REASONING", "").lower() == "true"
        self.ui_channel = getenv("UI_CHANNEL", "")
        self.ai_provider = getenv("AI_PROVIDER", "")
        self.db_path = getenv("DB_PATH", "")
        self.deepseek_api_key = getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url = getenv("DEEPSEEK_BASE_URL", "")
        self.deepseek_model = getenv("DEEPSEEK_MODEL", "")
        self.deepseek_thinking = getenv("DEEPSEEK_THINKING", "")
        self.deepseek_reasoning_effort = getenv("DEEPSEEK_REASONING_EFFORT", "")
        self.deepseek_max_tokens = int(getenv("DEEPSEEK_MAX_TOKENS", "0"))
