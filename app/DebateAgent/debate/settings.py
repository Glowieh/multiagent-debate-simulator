from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_FILE)


class DebateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    use_local_llm: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    bedrock_model_id: str = "eu.amazon.nova-micro-v1:0"
    max_turns_per_debater: int = Field(default=3, ge=1)
    max_tool_loops: int = Field(default=3, ge=1)
    wikipedia_user_agent: str = (
        "MultiAgentDebateBot/1.0 (https://github.com/Glowieh/multiagent-debate-simulator)"
    )
    wikipedia_max_retries: int = Field(default=3, ge=0)
    wikipedia_retry_wait: float = Field(default=1.0, ge=0)


_settings: DebateSettings | None = None


def get_settings() -> DebateSettings:
    global _settings
    if _settings is None:
        _settings = DebateSettings()
    return _settings


def use_local_llm() -> bool:
    return get_settings().use_local_llm
