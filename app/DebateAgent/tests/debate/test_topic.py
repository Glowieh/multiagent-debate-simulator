import pytest

from debate.topic import MAX_TOPIC_LENGTH, TopicValidationError, normalize_topic


def test_normalize_topic_strips_whitespace() -> None:
    assert normalize_topic("  hello world  ") == "hello world"


def test_normalize_topic_rejects_empty() -> None:
    with pytest.raises(TopicValidationError, match="empty"):
        normalize_topic("")


def test_normalize_topic_rejects_whitespace_only() -> None:
    with pytest.raises(TopicValidationError, match="empty"):
        normalize_topic("   \t\n")


def test_normalize_topic_rejects_non_string() -> None:
    with pytest.raises(TopicValidationError, match="string"):
        normalize_topic(123)


def test_normalize_topic_rejects_over_limit() -> None:
    with pytest.raises(TopicValidationError, match=str(MAX_TOPIC_LENGTH)):
        normalize_topic("x" * (MAX_TOPIC_LENGTH + 1))


def test_normalize_topic_accepts_at_limit() -> None:
    topic = "x" * MAX_TOPIC_LENGTH
    assert normalize_topic(topic) == topic
