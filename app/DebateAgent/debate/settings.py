from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DebateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    use_local_llm: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    bedrock_model_id: str = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
    max_turns_per_debater: int = Field(default=3, ge=1)
    max_tool_loops: int = Field(default=3, ge=1)


_settings: DebateSettings | None = None


def get_settings() -> DebateSettings:
    global _settings
    if _settings is None:
        _settings = DebateSettings()
    return _settings


def use_local_llm() -> bool:
    return get_settings().use_local_llm
