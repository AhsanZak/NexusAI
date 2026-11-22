"""HTTP client for the OpenFGA check API. This module does not issue JWTs."""

from typing import Any, Protocol

import httpx

from app.authz.demo import AUTHORIZATION_MODEL, TUPLES


class OpenFGAError(Exception):
    """The OpenFGA server could not answer an authorization call."""


class PermissionChecker(Protocol):
    async def check(self, user: str, relation: str, object_id: str) -> bool:
        """Return whether OpenFGA allows this user, relation, and object."""


class OpenFGAClient:
    """Writes the demo model once, then performs Check calls."""

    def __init__(
        self,
        api_url: str,
        store_name: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.store_name = store_name
        self._transport = transport
        self.store_id = ""
        self.model_id = ""

    async def prepare(self) -> None:
        if self.store_id and self.model_id:
            return
        await self._prepare_once()

    async def check(self, user: str, relation: str, object_id: str) -> bool:
        if not self.store_id or not self.model_id:
            await self.prepare()
        try:
            return await self._check(user, relation, object_id)
        except OpenFGAError:
            self.store_id = ""
            self.model_id = ""
            await self.prepare()
            return await self._check(user, relation, object_id)

    async def _check(self, user: str, relation: str, object_id: str) -> bool:
        payload = {
            "tuple_key": {"user": user, "relation": relation, "object": object_id},
            "authorization_model_id": self.model_id,
        }
        body = await self._request("POST", f"/stores/{self.store_id}/check", payload)
        return bool(body.get("allowed"))

    async def _prepare_once(self) -> None:
        self.store_id = await self._find_or_create_store()
        written = await self._request(
            "POST",
            f"/stores/{self.store_id}/authorization-models",
            AUTHORIZATION_MODEL,
        )
        model_id = written.get("authorization_model_id")
        if not isinstance(model_id, str) or not model_id:
            raise OpenFGAError("OpenFGA did not return an authorization model id")
        self.model_id = model_id
        tuple_keys = [
            {"user": user, "relation": relation, "object": object_id}
            for user, relation, object_id in TUPLES
        ]
        await self._request(
            "POST",
            f"/stores/{self.store_id}/write",
            {"writes": {"tuple_keys": tuple_keys, "on_duplicate": "ignore"}},
        )

    async def _find_or_create_store(self) -> str:
        listed = await self._request("GET", "/stores")
        stores = listed.get("stores")
        if isinstance(stores, list):
            for store in stores:
                if isinstance(store, dict) and store.get("name") == self.store_name:
                    store_id = store.get("id")
                    if isinstance(store_id, str) and store_id:
                        return store_id
        created = await self._request("POST", "/stores", {"name": self.store_name})
        store_id = created.get("id")
        if not isinstance(store_id, str) or not store_id:
            raise OpenFGAError("OpenFGA did not return a store id")
        return store_id

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.api_url,
                timeout=10,
                transport=self._transport,
            ) as client:
                response = await client.request(method, path, json=payload)
        except httpx.HTTPError as exc:
            raise OpenFGAError("OpenFGA is not running") from exc
        if response.status_code >= 400:
            detail = response.text[:300] or response.reason_phrase
            raise OpenFGAError(f"OpenFGA returned HTTP {response.status_code}: {detail}")
        if not response.content:
            return {}
        body = response.json()
        if not isinstance(body, dict):
            raise OpenFGAError("OpenFGA returned an unexpected payload")
        return body
