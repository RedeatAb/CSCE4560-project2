
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User


def test_create_user(client: TestClient, db: Session) -> None:

    # Generate a unique email for each test run
    email = f"pollo-{uuid.uuid4().hex}@example.com"

    # Create a new user through the API
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    # Check that the user was created successfully
    assert r.status_code == 200

    data = r.json()

    # Find the new user in the database
    user = db.exec(
        select(User).where(User.id == data["id"])
    ).first()

    # Verify the saved user information
    assert user is not None
    assert user.email == email
    assert user.full_name == "Pollo Listo"

