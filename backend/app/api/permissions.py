"""Super-admin CRUD for the OpenFGA grants members and guests are checked against."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import require_super_admin
from app.authz.client import OpenFGAError, get_openfga_client
from app.authz.demo import InvalidGrant
from app.models.user import User
from app.repositories.grants import DuplicateGrantError, GrantNotFound
from app.schemas.access import (
    GrantCreateRequest,
    GrantResponse,
    GrantUpdateRequest,
    PermissionListResponse,
)
from app.services.access import (
    create_permission,
    delete_permission,
    list_permissions,
    update_permission,
)

router = APIRouter(prefix="/admin/permissions", tags=["admin"])


def _openfga_error(exc: OpenFGAError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get("", response_model=PermissionListResponse)
async def permissions(
    _admin: Annotated[User, Depends(require_super_admin)],
) -> PermissionListResponse:
    try:
        return await list_permissions(get_openfga_client())
    except OpenFGAError as exc:
        raise _openfga_error(exc) from exc


@router.post("", response_model=GrantResponse, status_code=status.HTTP_201_CREATED)
async def add_permission(
    body: GrantCreateRequest,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> GrantResponse:
    try:
        return await create_permission(
            get_openfga_client(),
            body.subject_kind,
            body.user_id,
            body.relation,
            body.object_id,
        )
    except InvalidGrant as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except GrantNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That member does not exist",
        ) from exc
    except DuplicateGrantError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That permission is already granted",
        ) from exc
    except OpenFGAError as exc:
        raise _openfga_error(exc) from exc


@router.patch("/{grant_id}", response_model=GrantResponse)
async def change_permission(
    grant_id: uuid.UUID,
    body: GrantUpdateRequest,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> GrantResponse:
    try:
        return await update_permission(get_openfga_client(), grant_id, body.relation)
    except InvalidGrant as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except GrantNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That permission was not found",
        ) from exc
    except DuplicateGrantError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That permission is already granted",
        ) from exc
    except OpenFGAError as exc:
        raise _openfga_error(exc) from exc


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission(
    grant_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> None:
    try:
        await delete_permission(get_openfga_client(), grant_id)
    except GrantNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That permission was not found",
        ) from exc
    except OpenFGAError as exc:
        raise _openfga_error(exc) from exc
