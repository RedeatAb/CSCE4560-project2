
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session

from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import ShoppingCart


# Check the signed cart JWT and verify ownership
def get_current_cart(
    session: SessionDep,
    current_user: CurrentUser,
    x_cart_token: Annotated[str, Header()],
) -> ShoppingCart:

    # Decode the JWT and verify its signature and expiration
    try:
        payload = jwt.decode(
            x_cart_token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )

        # Make sure this is a shopping cart token
        if payload.get("token_type") != "cart":
            raise ValueError("Invalid token type")

        # Convert the token's cart ID into a UUID
        cart_id = uuid.UUID(payload["sub"])

        # Project 2 requires a time-based UUID (version 1)
        if cart_id.version != 1:
            raise ValueError("Invalid cart ID")

        # Verify that the token belongs to the logged-in user
        if payload.get("owner_id") != str(current_user.id):
            raise ValueError("Cart owner mismatch")

        # Extract the creation time embedded in the UUID
        uuid_timestamp = datetime.fromtimestamp(
            (cart_id.time - 0x01B21DD213814000) / 10_000_000,
            tz=timezone.utc,
        )

        now = datetime.now(timezone.utc)

        # Reject UUIDs from the future or older than one hour
        if not (uuid_timestamp <= now <= uuid_timestamp + timedelta(hours=1)):
            raise ValueError("Cart ID has expired")

    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired shopping cart token",
        )

    # Retrieve the shopping cart from PostgreSQL
    cart = session.get(ShoppingCart, cart_id)

    if cart is None:
        raise HTTPException(status_code=404, detail="Shopping cart not found")

    # Verify ownership against the actual database record
    if cart.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Reject inactive carts
    if not cart.active:
        raise HTTPException(status_code=403, detail="Shopping cart is inactive")

    # Reject expired carts
    cart_expires = cart.expires
    if cart_expires.tzinfo is None:
        cart_expires = cart_expires.replace(tzinfo=timezone.utc)

    if cart_expires <= datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Shopping cart has expired")

    return cart


# Reusable dependency for protected shopping cart routes
CurrentCart = Annotated[ShoppingCart, Depends(get_current_cart)]
