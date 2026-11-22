"""Responses for the OpenFGA demonstration."""

from pydantic import BaseModel


class AccessDecisionResponse(BaseModel):
    user_id: str
    display_name: str
    role: str
    relation: str
    object_id: str
    object_name: str
    shared: bool
    allowed: bool
    content: str | None


class AuthzDemoResponse(BaseModel):
    store_id: str
    authorization_model_id: str
    api_url: str
    decisions: list[AccessDecisionResponse]
