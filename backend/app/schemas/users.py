"""Login and admin user payloads. Password hashes are never returned."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: str
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    role: str = "member"
