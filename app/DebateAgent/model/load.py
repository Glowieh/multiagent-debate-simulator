from langchain_aws import ChatBedrock
from langchain_core.language_models.chat_models import BaseChatModel

from debate.settings import DebateSettings, get_settings

_model: BaseChatModel | None = None


def _create_model(settings: DebateSettings) -> BaseChatModel:
    if settings.use_local_llm:
        from langchain_ollama import ChatOllama

        kwargs: dict[str, object] = {
            "model": settings.ollama_model,
            "base_url": settings.ollama_base_url,
        }
        if settings.llm_request_timeout_seconds is not None:
            kwargs["timeout"] = settings.llm_request_timeout_seconds
        return ChatOllama(**kwargs)  # pyright: ignore[reportArgumentType]

    bedrock_kwargs: dict[str, object] = {"model": settings.bedrock_model_id}
    if settings.llm_request_timeout_seconds is not None:
        from botocore.config import Config

        bedrock_kwargs["config"] = Config(
            read_timeout=settings.llm_request_timeout_seconds
        )
    return ChatBedrock(**bedrock_kwargs)  # pyright: ignore[reportArgumentType]


def load_model() -> BaseChatModel:
    global _model
    if _model is None:
        _model = _create_model(get_settings())
    return _model


def reset_model_cache() -> None:
    global _model
    _model = None
