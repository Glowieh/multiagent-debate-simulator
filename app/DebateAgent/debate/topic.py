"""Shared debate topic validation."""

from __future__ import annotations

MAX_TOPIC_LENGTH = 500


class TopicValidationError(ValueError):
    """Raised when a debate topic fails validation."""


def normalize_topic(raw: object) -> str:
    if not isinstance(raw, str):
        raise TopicValidationError("Topic must be a string")

    topic = raw.strip()
    if not topic:
        raise TopicValidationError("Topic cannot be empty")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise TopicValidationError(
            f"Topic cannot exceed {MAX_TOPIC_LENGTH} characters"
        )

    return topic
