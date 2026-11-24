"""Name the chat route and check whether each model option answers."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.ai.choices import NAMES, active_choice_id, model_choices
from app.ai.gateway import scrub
from app.core.config import Settings

Probe = Callable[[str, dict[str, str]], Awaitable[tuple[int, str]]]


@dataclass(frozen=True)
class ProviderCheck:
    id: str
    name: str
    state: str
    active: bool
    detail: str


def active_route(settings: Settings) -> tuple[str, str]:
    """Return the route id and the label shown in the UI."""
    choice_id = active_choice_id(settings)
    return choice_id, NAMES.get(choice_id, "Other")


def configured_model_name(settings: Settings) -> str:
    model = settings.chat_model.strip()
    if "/" in model:
        return model.split("/", 1)[1]
    return model


async def check_providers(settings: Settings, probe: Probe | None = None) -> list[ProviderCheck]:
    fetch = probe or _probe
    selected = active_choice_id(settings)
    choices = await model_choices(settings, fetch)
    return [
        ProviderCheck(item.id, item.name, item.state, item.id == selected, item.detail)
        for item in choices
    ]


async def _probe(url: str, headers: dict[str, str]) -> tuple[int, str]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        return 0, scrub(str(exc)) or type(exc).__name__
    return response.status_code, scrub(response.text[:8000]) or ""


