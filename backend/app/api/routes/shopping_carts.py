
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
from fastapi import APIRouter, status
from sqlmodel import SQLModel

from app.api.cart_security import CurrentCart
from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import ShoppingCart, ShoppingCartPublic
from app.models import Message
from typing import Annotated

from fastapi import Depends

from app.api.deps import get_current_active_superuser
from app.models import Message
from fastapi import APIRouter, HTTPException, status

# Router for shopping cart endpoints
router = APIRouter(
    prefix="/shopping-carts",
    tags=["shopping-carts"]
)


# Response returned after creating a shopping cart
class CartCreateResponse(SQLModel):
    cart_id: uuid.UUID
    cart_token: str
    message: str


# ==================================================
# POST - CREATE SHOPPING CART
# ==================================================

@router.post(
    "/",
    response_model=CartCreateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_shopping_cart(
    session: SessionDep,
    current_user: CurrentUser,
):
    # Set the cart expiration to one hour from now
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)

    # Create a new cart belonging to the logged-in user
    cart = ShoppingCart(
        session_key=str(uuid.uuid4()),
        active=True,
        expires=expiration,
        total=Decimal("0.00"),
        owner_id=current_user.id,
    )

    # Save the cart to PostgreSQL
    session.add(cart)
    session.commit()
    session.refresh(cart)

    # Generate a signed JWT containing the cart ID
    cart_token = jwt.encode(
        {
            "sub": str(cart.id),
            "owner_id": str(current_user.id),
            "token_type": "cart",
            "exp": expiration,
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    # Return the cart ID and signed JWT
    return CartCreateResponse(
        cart_id=cart.id,
        cart_token=cart_token,
        message="Shopping cart created successfully",
    )


# ==================================================
# GET - VIEW SHOPPING CART
# ==================================================

@router.get(
    "/",
    response_model=ShoppingCartPublic
)
def get_shopping_cart(
    current_cart: CurrentCart,
):
    # CurrentCart verifies the cart JWT, expiration,
    # UUID age, and authenticated user's ownership
    return current_cart

# ==================================================
# DELETE - REMOVE SHOPPING CART
# ==================================================

@router.delete(
    "/",
    response_model=Message
)
def delete_shopping_cart(
    session: SessionDep,
    current_cart: CurrentCart,
):
    # CurrentCart verifies the JWT and cart ownership

    # Delete the cart's links to its cart items
    current_cart.cart_items.clear()

    # Delete the shopping cart from PostgreSQL
    session.delete(current_cart)
    session.commit()

    # Return confirmation
    return Message(message="Shopping cart deleted successfully")


# ==================================================
# ADMIN - VIEW ANY USER'S SHOPPING CART
# ==================================================

@router.get(
    "/admin/{cart_id}",
    response_model=ShoppingCartPublic
)
def admin_get_shopping_cart(
    session: SessionDep,
    cart_id: uuid.UUID,
    admin: Annotated[
        object,
        Depends(get_current_active_superuser)
    ],
):
    # Admin authentication is checked automatically

    # Find the requested shopping cart
    cart = session.get(ShoppingCart, cart_id)

    if cart is None:
        raise HTTPException(
            status_code=404,
            detail="Shopping cart not found"
        )

    return cart


# ==================================================
# ADMIN - DELETE ANY USER'S SHOPPING CART
# ==================================================

@router.delete(
    "/admin/{cart_id}",
    response_model=Message
)
def admin_delete_shopping_cart(
    session: SessionDep,
    cart_id: uuid.UUID,
    admin: Annotated[
        object,
        Depends(get_current_active_superuser)
    ],
):
    # Find the requested shopping cart
    cart = session.get(ShoppingCart, cart_id)

    if cart is None:
        raise HTTPException(
            status_code=404,
            detail="Shopping cart not found"
        )

    # Remove the cart-item associations
    cart.cart_items.clear()

    # Delete the shopping cart
    session.delete(cart)
    session.commit()

    return Message(
        message="Shopping cart deleted by administrator"
    )
