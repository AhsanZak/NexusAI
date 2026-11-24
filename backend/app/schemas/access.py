"""Admin grant CRUD and the signed-in member's OpenFGA view."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    object_id: str
    name: str
    object_type: str
    releasing_relation: str
    relations: list[str]


class GrantResponse(BaseModel):
    id: UUID
    subject: str
    actor: Literal["member", "guest"]
    user_id: UUID | None
    display_name: str
    email: str | None
    relation: str
    object_id: str
    object_name: str
    object_type: str
    created_at: datetime


class PermissionListResponse(BaseModel):
    catalog: list[CatalogItem]
    grants: list[GrantResponse]


class GrantCreateRequest(BaseModel):
    subject_kind: Literal["member", "guest"]
    user_id: UUID | None = None
    relation: str = Field(min_length=1, max_length=32)
    object_id: str = Field(min_length=3, max_length=200)


class GrantUpdateRequest(BaseModel):
    relation: str = Field(min_length=1, max_length=32)


class FeatureView(BaseModel):
    object_id: str
    name: str
    allowed: bool


class DocumentView(BaseModel):
    object_id: str
    object_name: str
    relation: str
    actor: Literal["member", "super_admin"]
    allowed: bool
    guest_allowed: bool
    content: str | None


class AssignmentView(BaseModel):
    relation: str
    object_id: str
    object_name: str
    object_type: str
    actor: Literal["member", "guest"]


class MyAccessResponse(BaseModel):
    actor: Literal["member", "super_admin"]
    subject: str
    display_name: str
    email: str
    role: str
    features: list[FeatureView]
    documents: list[DocumentView]
    assignments: list[AssignmentView]
    guest_assignments: list[AssignmentView]
