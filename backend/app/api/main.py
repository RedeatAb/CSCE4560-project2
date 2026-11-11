
from fastapi import APIRouter

from app.api.routes import (
    items,
    login,
    private,
    users,
    utils,
    shopping_carts,
    cart_items,
)
from app.core.config import settings

# Main API router
api_router = APIRouter()

# Existing application routes
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# Shopping cart routes
api_router.include_router(shopping_carts.router)

# Cart item routes
api_router.include_router(cart_items.router)

# Development-only routes
if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
