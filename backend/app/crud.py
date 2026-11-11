
import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate


# ==================================================
# CREATE USER
# ==================================================

def create_user(*, session: Session, user_create: UserCreate) -> User:

    # Convert user input into a database user
    # and hash the password before saving.
    db_obj = User.model_validate(
        user_create,
        update={
            "hashed_password": get_password_hash(user_create.password)
        }
    )

    # Save the user to the database
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    return db_obj


# ==================================================
# UPDATE USER
# ==================================================

def update_user(
    *,
    session: Session,
    db_user: User,
    user_in: UserUpdate
) -> Any:

    # Get only the fields the user wants to update
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}

    # Hash the new password if one was provided
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password

    # Update the user information
    db_user.sqlmodel_update(user_data, update=extra_data)

    # Save changes to the database
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


# ==================================================
# FIND USER BY EMAIL
# ==================================================

def get_user_by_email(
    *,
    session: Session,
    email: str
) -> User | None:

    # Search for the user using their email
    statement = select(User).where(User.email == email)

    session_user = session.exec(statement).first()

    return session_user


# ==================================================
# DUMMY HASH FOR LOGIN SECURITY
# ==================================================

# Used when an email does not exist in the database.
# Helps reduce timing differences during authentication.
DUMMY_HASH = get_password_hash("dummy-password-not-for-login")


# ==================================================
# AUTHENTICATE USER
# ==================================================

def authenticate(
    *,
    session: Session,
    email: str,
    password: str
) -> User | None:

    # Find the user by email
    db_user = get_user_by_email(
        session=session,
        email=email
    )

    # If the user does not exist, perform a dummy check
    if not db_user:
        verify_password(password, DUMMY_HASH)
        return None

    # Verify the entered password
    # and check if the hash needs upgrading
    verified, updated_password_hash = verify_password(
        password,
        db_user.hashed_password
    )

    # Reject incorrect passwords
    if not verified:
        return None

    # Upgrade old bcrypt passwords to Argon2
    if updated_password_hash is not None:

        db_user.hashed_password = updated_password_hash

        # Save the upgraded password hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    # Return the authenticated user
    return db_user


# ==================================================
# CREATE ITEM
# ==================================================

def create_item(
    *,
    session: Session,
    item_in: ItemCreate,
    owner_id: uuid.UUID
) -> Item:

    # Create a new item belonging to the user
    db_item = Item.model_validate(
        item_in,
        update={
            "owner_id": owner_id
        }
    )

    # Save the item to the database
    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    return db_item
