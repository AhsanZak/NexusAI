"""OpenFGA demonstration. The route identifies nobody; Check decides the text."""

from fastapi import APIRouter, HTTPException, status

from app.authz.client import OpenFGAError, get_openfga_client
from app.schemas.authz import AccessDecisionResponse, AuthzDemoResponse
from app.services.authorization import collect_decisions

router = APIRouter(prefix="/authz", tags=["authz"])


@router.get("/demo", response_model=AuthzDemoResponse)
async def authorization_demo() -> AuthzDemoResponse:
    """Run the two-user example against the configured OpenFGA server."""
    client = get_openfga_client()
    try:
        await client.prepare()
        decisions = await collect_decisions(client)
    except OpenFGAError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return AuthzDemoResponse(
        store_id=client.store_id,
        authorization_model_id=client.model_id,
        api_url=client.api_url,
        decisions=[
            AccessDecisionResponse(
                user_id=item.user_id,
                display_name=item.display_name,
                role=item.role,
                relation=item.relation,
                object_id=item.object_id,
                object_name=item.object_name,
                shared=item.shared,
                allowed=item.allowed,
                content=item.content,
            )
            for item in decisions
        ],
    )
