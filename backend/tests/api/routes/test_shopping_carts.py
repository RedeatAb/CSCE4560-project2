
import uuid

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core import security


# TEST 1: Create a shopping cart and verify its JWT
def test_create_shopping_cart(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    response = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 201
    data = response.json()

    assert "cart_id" in data
    assert "cart_token" in data
    assert uuid.UUID(data["cart_id"]).version == 1

    payload = jwt.decode(
        data["cart_token"],
        settings.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )

    assert payload["sub"] == data["cart_id"]
    assert payload["token_type"] == "cart"


# TEST 2: Read a shopping cart using its token
def test_get_shopping_cart(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    created = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert created.status_code == 201
    cart = created.json()

    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers={
            **normal_user_token_headers,
            "x-cart-token": cart["cart_token"],
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == cart["cart_id"]


# TEST 3: Reject invalid shopping cart tokens
def test_invalid_cart_token(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers={
            **normal_user_token_headers,
            "x-cart-token": "invalid-token",
        },
    )

    assert response.status_code == 403


# TEST 4: Admin can view another user's cart
def test_admin_get_shopping_cart(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:

    created = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert created.status_code == 201
    cart_id = created.json()["cart_id"]

    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/admin/{cart_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == cart_id


# TEST 5: Regular users cannot access admin endpoints
def test_regular_user_cannot_access_admin(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/admin/{uuid.uuid1()}",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 403


# TEST 6: Reject missing cart token
def test_missing_cart_token(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    # Request a cart without providing x-cart-token
    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    # Missing required header should return 422
    assert response.status_code == 422


# TEST 7: Reject expired cart token
def test_expired_cart_token(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    from datetime import datetime, timedelta, timezone

    # Create a shopping cart
    created = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert created.status_code == 201

    # Decode the original token
    cart = created.json()
    payload = jwt.decode(
        cart["cart_token"],
        settings.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )

    # Change expiration to one minute ago
    payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)

    expired_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    # Attempt to access the cart with an expired token
    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers={
            **normal_user_token_headers,
            "x-cart-token": expired_token,
        },
    )

    assert response.status_code == 403


# TEST 8: Reject token with incorrect owner
def test_wrong_cart_owner(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    # Create a shopping cart
    created = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert created.status_code == 201

    cart = created.json()

    # Decode the cart JWT
    payload = jwt.decode(
        cart["cart_token"],
        settings.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )

    # Replace owner ID with a different UUID
    payload["owner_id"] = str(uuid.uuid4())

    wrong_owner_token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    # Attempt to access cart with mismatched owner
    response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers={
            **normal_user_token_headers,
            "x-cart-token": wrong_owner_token,
        },
    )

    assert response.status_code == 403

# TEST 9: Delete a shopping cart
def test_delete_shopping_cart(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:

    # Create a shopping cart
    created = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert created.status_code == 201
    cart = created.json()

    # Include both authentication tokens
    headers = {
        **normal_user_token_headers,
        "x-cart-token": cart["cart_token"],
    }

    # Delete the shopping cart
    response = client.delete(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=headers,
    )

    assert response.status_code == 200

    # Verify the deleted cart can no longer be accessed
    get_response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=headers,
    )

    assert get_response.status_code == 404


# Helper: Create a cart and an existing database item
def setup_cart_item_test(client, normal_user_token_headers):
    # Create a shopping cart
    cart_response = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )
    assert cart_response.status_code == 201

    cart = cart_response.json()
    headers = {
        **normal_user_token_headers,
        "x-cart-token": cart["cart_token"],
    }

    # Create an item owned by the logged-in user
    item_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        json={
            "title": f"Test Item {uuid.uuid4()}",
            "description": "Shopping cart test item",
        },
    )
    assert item_response.status_code == 200

    item_id = item_response.json()["id"]
    return headers, item_id


# TEST 10: Add an item to the shopping cart
def test_add_cart_item(client, normal_user_token_headers):
    headers, item_id = setup_cart_item_test(
        client, normal_user_token_headers
    )

    response = client.post(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
        json={
            "item_id": item_id,
            "quantity": 2,
            "unit_price": "25.00",
            "description": "Test product",
        },
    )

    assert response.status_code == 201
    assert response.json()["quantity"] == 2


# TEST 11: Retrieve shopping cart items
def test_get_cart_items(client, normal_user_token_headers):
    headers, item_id = setup_cart_item_test(
        client, normal_user_token_headers
    )

    client.post(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
        json={
            "item_id": item_id,
            "quantity": 1,
            "unit_price": "15.00",
        },
    )

    response = client.get(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


# TEST 12: Update cart item quantity
def test_update_cart_item(client, normal_user_token_headers):
    headers, item_id = setup_cart_item_test(
        client, normal_user_token_headers
    )

    created = client.post(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
        json={
            "item_id": item_id,
            "quantity": 1,
            "unit_price": "20.00",
        },
    )
    assert created.status_code == 201

    cart_item_id = created.json()["id"]

    response = client.patch(
        f"{settings.API_V1_STR}/cart-items/{cart_item_id}",
        headers=headers,
        json={"quantity": 3},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 3


# TEST 13: Delete a cart item
def test_delete_cart_item(client, normal_user_token_headers):
    headers, item_id = setup_cart_item_test(
        client, normal_user_token_headers
    )

    created = client.post(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
        json={
            "item_id": item_id,
            "quantity": 1,
            "unit_price": "10.00",
        },
    )
    assert created.status_code == 201

    cart_item_id = created.json()["id"]

    response = client.delete(
        f"{settings.API_V1_STR}/cart-items/{cart_item_id}",
        headers=headers,
    )

    assert response.status_code == 200

    remaining = client.get(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
    )

    assert remaining.status_code == 200
    assert remaining.json()["count"] == 0


# TEST 14: Verify shopping cart total calculation
def test_cart_total_calculation(client, normal_user_token_headers):
    headers, item_id = setup_cart_item_test(
        client, normal_user_token_headers
    )

    created = client.post(
        f"{settings.API_V1_STR}/cart-items/",
        headers=headers,
        json={
            "item_id": item_id,
            "quantity": 2,
            "unit_price": "25.00",
        },
    )
    assert created.status_code == 201

    cart_response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=headers,
    )

    assert cart_response.status_code == 200
    assert float(cart_response.json()["total"]) == 50.00

# TEST 15: Admin can delete another user's shopping cart
def test_admin_delete_shopping_cart(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:

    # Regular user creates a shopping cart
    created = client.post(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers=normal_user_token_headers,
    )

    assert created.status_code == 201
    cart = created.json()

    # Admin deletes the regular user's cart
    response = client.delete(
        f"{settings.API_V1_STR}/shopping-carts/admin/{cart['cart_id']}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200

    # Confirm the deleted cart is no longer accessible
    get_response = client.get(
        f"{settings.API_V1_STR}/shopping-carts/",
        headers={
            **normal_user_token_headers,
            "x-cart-token": cart["cart_token"],
        },
    )

    assert get_response.status_code == 404
