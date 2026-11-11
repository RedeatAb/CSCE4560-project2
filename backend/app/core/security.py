
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings


# Algorithm used for JWT authentication
ALGORITHM = "HS256"


# ==================================================
# PASSWORD HASH CONFIGURATION
# ==================================================

# Argon2 is used for new passwords.
# Bcrypt is supported for existing passwords.
password_hash = PasswordHash((
    Argon2Hasher(),
    BcryptHasher(),
))


# ==================================================
# CREATE JWT ACCESS TOKEN
# ==================================================

def create_access_token(
    subject: str | Any,
    expires_delta: timedelta
) -> str:

    # Set the token expiration time
    expire = datetime.now(timezone.utc) + expires_delta

    # Store the expiration and user ID in the token
    to_encode = {
        "exp": expire,
        "sub": str(subject)
    }

    # Generate and sign the JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ==================================================
# HASH PASSWORD USING ARGON2
# ==================================================

def get_password_hash(password: str) -> str:

    # Hash the password using Argon2
    hashed_password = password_hash.hash(password)

    return hashed_password


# ==================================================
# VERIFY PASSWORD
# ==================================================

def verify_password(
    plain_password: str,
    hashed_password: str
) -> tuple[bool, str | None]:

    # Verify the entered password.
    # Also check if an older bcrypt hash needs upgrading.
    verified, updated_password_hash = (
        password_hash.verify_and_update(
            plain_password,
            hashed_password
        )
    )

    # Return whether the password is correct
    # and the upgraded hash if one was generated.
    return verified, updated_password_hash
