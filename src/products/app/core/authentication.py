from typing import List, Annotated
import logging

from fastapi import Depends, HTTPException, status, Request
from keycloak import KeycloakOpenID
from pydantic import BaseModel

from core.config import settings


class MockUser(BaseModel):
    sub: str | None = None
    username: str | None = None
    name: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    permissions: List[str] = []


def get_keycloak_client():
    try:
        keycloak_openid = KeycloakOpenID(
            server_url=f"{settings.KEYCLOAK_SERVER_URL}/auth",
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM_NAME,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY,
        )
        keycloak_openid.well_known()
        return keycloak_openid
    except Exception as e:
        logging.exception("Error configuring Keycloak client")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error configuring Keycloak client"
        )


async def keycloak_auth(request: Request, keycloak_openid=Depends(get_keycloak_client)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header.split("Bearer ")[-1]

    try:
        user_info = keycloak_openid.decode_token(token)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user = MockUser(
            sub=user_info.get("sub"),
            username=user_info.get("preferred_username"),
            name=user_info.get("name"),
            email=user_info.get("email"),
            first_name=user_info.get("given_name"),
            last_name=user_info.get("family_name"),
            permissions=user_info.get("realm_access", {}).get("roles", []),
        )
        return user

    except Exception as e:
        logging.exception("Error decoding token or retrieving user info")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


CurrentUserDep = Annotated[MockUser, Depends(keycloak_auth)]


def StaffOnly(user: CurrentUserDep):
    if "staff" not in user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff permission required"
        )
    return user


StaffUserDep = Annotated[MockUser, Depends(StaffOnly)]
