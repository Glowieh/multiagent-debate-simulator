from langchain_aws import ChatBedrock
from langchain_core.language_models.chat_models import BaseChatModel

from debate.settings import DebateSettings, get_settings

_model: BaseChatModel | None = None


def _create_model(settings: DebateSettings) -> BaseChatModel:
    if settings.use_local_llm:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    return ChatBedrock(model=settings.bedrock_model_id)


def load_model() -> BaseChatModel:
    global _model
    if _model is None:
        _model = _create_model(get_settings())
    return _model


def reset_model_cache() -> None:
    global _model
    _model = None
