"""The intent of a question is read from that chat, not from another chat."""

from app.intent import apply_intent, classify_intent
from app.intent.classify import parse_intent_name, parse_router_result
from app.intent.router import _user_text
from app.services.assistant import messages_for


def test_a_follow_up_uses_only_this_chat() -> None:
    prior = [
        {"role": "user", "content": "The site code for Cairo is ZX-44."},
        {"role": "assistant", "content": "Cairo is ZX-44."},
    ]
    intent = classify_intent("Which of those did you name first?", prior)
    sent = apply_intent(messages_for([], "Which of those did you name first?", prior), intent)
    text = "\n".join(str(item["content"]) for item in sent)

    assert intent.name == "follow_up"
    assert intent.label == "Follow-up"
    assert "ZX-44" in text
    assert "QM-17" not in text
    assert intent.needs_documents is True
    assert "not allowed to use it" in text


def test_a_question_that_does_not_need_documents_skips_them() -> None:
    prior = [{"role": "assistant", "content": "World Bank indicators."}]
    intent = classify_intent("which ai are you ?", prior)
    sent = apply_intent(
        messages_for([], "which ai are you ?", prior, needs_documents=intent.needs_documents),
        intent,
    )
    text = "\n".join(str(item["content"]) for item in sent)

    assert "not allowed to use it" not in text
    assert "Documents:" not in text
    assert "World Bank indicators." in text
    assert "Answer the question directly" in text


def test_named_intents() -> None:
    assert classify_intent("What documents am I allowed to use?", None).name == "access"
    assert classify_intent("Summarize the finance notes", None).name == "summary"
    assert classify_intent("What do the tables say?", None).name == "lookup"
    assert classify_intent("Hello", None).name == "new_topic"
    assert classify_intent("Which of those did you name first?", None).name == "new_topic"
    earlier = [{"role": "assistant", "content": "World Bank indicators."}]
    direct = classify_intent("which ai are you ?", earlier)
    assert direct.name == "new_topic"
    assert direct.needs_documents is False


def test_router_json_is_one_of_the_known_intents() -> None:
    assert parse_intent_name('{"intent":"follow_up"}') == "follow_up"
    assert parse_intent_name("thinking\n{\"intent\":\"summary\"}") == "summary"
    assert parse_intent_name('{"intent":"other"}') is None
    assert parse_intent_name('{"intent":"identity"}') is None
    assert parse_router_result('{"intent":"new_topic","needs_documents":false}') == (
        "new_topic",
        False,
    )


def test_router_prompt_contains_only_this_chat() -> None:
    prior = [{"role": "user", "content": "Cairo is ZX-44."}]
    text = _user_text("Which of those?", prior)

    assert "ZX-44" in text
    assert "QM-17" not in text
