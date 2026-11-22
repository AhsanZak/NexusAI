"""OpenFGA demo decisions withhold text unless Check allows it."""

import json

import httpx
import pytest

from app.authz.client import OpenFGAClient
from app.authz.demo import DOCUMENTS, TUPLES, USERS
from app.services.authorization import collect_decisions


class _ScriptedChecker:
    def __init__(self, allowed: set[tuple[str, str, str]]) -> None:
        self.allowed = allowed
        self.calls: list[tuple[str, str, str]] = []

    async def check(self, user: str, relation: str, object_id: str) -> bool:
        self.calls.append((user, relation, object_id))
        return (user, relation, object_id) in self.allowed


@pytest.mark.asyncio
async def test_shared_permission_and_two_private_permissions() -> None:
    checker = _ScriptedChecker(set(TUPLES))
    decisions = await collect_decisions(checker)
    by_user = {
        user.user_id: [item for item in decisions if item.user_id == user.user_id] for user in USERS
    }

    amina = {item.object_id: item for item in by_user["user:amina"]}
    luis = {item.object_id: item for item in by_user["user:luis"]}

    assert amina["document:world-bank"].allowed is True
    assert luis["document:world-bank"].allowed is True
    assert amina["document:world-bank"].shared is True
    assert amina["document:world-bank"].content == DOCUMENTS[0].content
    assert luis["document:world-bank"].content == DOCUMENTS[0].content

    assert amina["document:olist-sales"].allowed is True
    assert amina["document:olist-sales"].shared is False
    assert "2016–2018" in (amina["document:olist-sales"].content or "")
    assert luis["document:olist-sales"].allowed is False
    assert luis["document:olist-sales"].content is None

    assert luis["document:finance-reviews"].allowed is True
    assert luis["document:finance-reviews"].shared is False
    assert amina["document:finance-reviews"].allowed is False
    assert amina["document:finance-reviews"].content is None
    assert len(checker.calls) == len(USERS) * len(DOCUMENTS)


@pytest.mark.asyncio
async def test_openfga_client_writes_the_model_and_reads_check() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/stores":
            return httpx.Response(200, json={"stores": []})
        if request.method == "POST" and request.url.path == "/stores":
            return httpx.Response(200, json={"id": "store-1", "name": "nexusai"})
        if request.url.path == "/stores/store-1/authorization-models":
            body = json.loads(request.content.decode())
            assert body["schema_version"] == "1.1"
            return httpx.Response(200, json={"authorization_model_id": "model-1"})
        if request.url.path == "/stores/store-1/write":
            body = json.loads(request.content.decode())
            written = {
                (item["user"], item["relation"], item["object"])
                for item in body["writes"]["tuple_keys"]
            }
            assert written == set(TUPLES)
            assert body["writes"]["on_duplicate"] == "ignore"
            return httpx.Response(200, json={})
        if request.url.path == "/stores/store-1/check":
            body = json.loads(request.content.decode())
            key = body["tuple_key"]
            allowed = (key["user"], key["relation"], key["object"]) in set(TUPLES)
            assert body["authorization_model_id"] == "model-1"
            return httpx.Response(200, json={"allowed": allowed})
        return httpx.Response(404, json={"code": "missing"})

    client = OpenFGAClient("http://openfga.test", "nexusai", transport=httpx.MockTransport(handler))
    await client.prepare()
    assert await client.check("user:amina", "analyst", "document:olist-sales") is True
    assert await client.check("user:luis", "analyst", "document:olist-sales") is False
