
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.cart_security import CurrentCart
from app.api.deps import SessionDep
from app.models import (
    CartItem,
    CartItemCreate,
    CartItemPublic,
    CartItemUpdate,
    CartItemsPublic,
    Item,
    Message,
)

# Routes for managing items inside a shopping cart
router = APIRouter(
    prefix="/cart-items",
    tags=["cart-items"]
)

# ==================================================
# POST - ADD ITEM TO SHOPPING CART
# ==================================================

@router.post(
    "/",
    response_model=CartItemPublic,
    status_code=status.HTTP_201_CREATED
)
def create_cart_item(
    session: SessionDep,
    current_cart: CurrentCart,
    item_in: CartItemCreate,
):
    # Check if the item exists in the database
    item = session.get(Item, item_in.item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    # Make sure the item belongs to the logged-in user
    if item.owner_id != current_cart.owner_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot add another user's item"
        )

    # Create a new cart item
    cart_item = CartItem(
        item_id=item_in.item_id,
        quantity=item_in.quantity,
        unit_price=item_in.unit_price,
        description=item_in.description,
    )

    # Add the item to the shopping cart
    current_cart.cart_items.append(cart_item)

    # Update the shopping cart total
    current_cart.total += (
        cart_item.unit_price * cart_item.quantity
    )

    # Save changes to PostgreSQL
    session.add(cart_item)
    session.add(current_cart)
    session.commit()
    session.refresh(cart_item)

    # Return the newly created cart item
    return cart_item

# ==================================================
# GET - VIEW ALL CART ITEMS
# ==================================================

@router.get(
    "/",
    response_model=CartItemsPublic
)
def get_cart_items(
    current_cart: CurrentCart,
):
    # CurrentCart verifies the JWT and cart ownership

    # Get all items belonging to the current cart
    cart_items = current_cart.cart_items

    # Return the cart items and their total count
    return CartItemsPublic(
        data=cart_items,
        count=len(cart_items)
    )

# ==================================================
# PATCH - UPDATE A CART ITEM
# ==================================================

@router.patch(
    "/{cart_item_id}",
    response_model=CartItemPublic
)
def update_cart_item(
    session: SessionDep,
    current_cart: CurrentCart,
    cart_item_id: uuid.UUID,
    item_in: CartItemUpdate,
):
    # Find the item inside the authenticated user's cart
    cart_item = next(
        (
            item for item in current_cart.cart_items
            if item.id == cart_item_id
        ),
        None
    )

    # Reject items that are not in this cart
    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    # Get only the fields the user wants to update
    update_data = item_in.model_dump(exclude_unset=True)

    # Prevent null values for required fields
    if (
        update_data.get("quantity", 1) is None
        or update_data.get("unit_price", 0) is None
    ):
        raise HTTPException(
            status_code=422,
            detail="Quantity and unit price cannot be null"
        )

    # Subtract the item's previous value
    old_total = cart_item.unit_price * cart_item.quantity

    # Update the cart item
    cart_item.sqlmodel_update(update_data)

    # Calculate the item's new value
    new_total = cart_item.unit_price * cart_item.quantity

    # Adjust the shopping cart total
    current_cart.total = (
        current_cart.total - old_total + new_total
    )

    # Save the updated item and cart
    session.add(cart_item)
    session.add(current_cart)
    session.commit()
    session.refresh(cart_item)

    return cart_item

# ==================================================
# DELETE - REMOVE ITEM FROM SHOPPING CART
# ==================================================

@router.delete(
    "/{cart_item_id}",
    response_model=Message
)
def delete_cart_item(
    session: SessionDep,
    current_cart: CurrentCart,
    cart_item_id: uuid.UUID,
):
    # Find the item inside the current user's cart
    cart_item = next(
        (
            item for item in current_cart.cart_items
            if item.id == cart_item_id
        ),
        None
    )

    # Reject items that do not belong to this cart
    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    # Calculate the value being removed
    item_total = cart_item.unit_price * cart_item.quantity

    # Remove the item from the shopping cart relationship
    current_cart.cart_items.remove(cart_item)

    # Update the shopping cart total
    current_cart.total -= item_total

    # Delete the cart item record
    session.delete(cart_item)

    # Save changes to PostgreSQL
    session.add(current_cart)
    session.commit()

    return Message(
        message="Cart item deleted successfully"
    )
