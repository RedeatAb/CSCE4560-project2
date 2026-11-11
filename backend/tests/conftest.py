
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    Item,
    User,
    CartItem,
    ShoppingCart,
    CartItem_ShoppingCart_Link,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


# ==================================================
# DATABASE SETUP AND CLEANUP
# ==================================================

@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:

    with Session(engine) as session:

        # Initialize the database before tests
        init_db(session)

        yield session

        # Delete relationships first
        session.execute(delete(CartItem_ShoppingCart_Link))

        # Delete cart items before their referenced items
        session.execute(delete(CartItem))

        # Delete shopping carts before their owners
        session.execute(delete(ShoppingCart))

        # Delete items before users
        session.execute(delete(Item))
        session.execute(delete(User))

        # Save cleanup changes
        session.commit()


# ==================================================
# FASTAPI TEST CLIENT
# ==================================================

@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:

    with TestClient(app) as c:
        yield c


# ==================================================
# ADMIN AUTHENTICATION
# ==================================================

@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:

    return get_superuser_token_headers(client)


# ==================================================
# REGULAR USER AUTHENTICATION
# ==================================================

@pytest.fixture(scope="module")
def normal_user_token_headers(
    client: TestClient,
    db: Session
) -> dict[str, str]:

    return authentication_token_from_email(
        client=client,
        email=settings.EMAIL_TEST_USER,
        db=db
    )
