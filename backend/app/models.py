
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from pydantic import EmailStr, computed_field
from sqlalchemy import DateTime, Numeric, Index, UniqueConstraint, Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# =========================================================
# USER MODELS
# =========================================================

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    hashed_password: str

    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    # Existing relationship between users and items
    items: list["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True
    )

    # Project 2: A user can own multiple shopping carts
    shopping_carts: list["ShoppingCart"] = Relationship(
        back_populates="owner",
        cascade_delete=True
    )


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# =========================================================
# ITEM MODELS
# =========================================================

class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE"
    )

    owner: User | None = Relationship(
        back_populates="items"
    )


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# =========================================================
# GENERAL API MODELS
# =========================================================

class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# =========================================================
# HOMEWORK 3 - ACADEMIC TRACKING MODELS
# =========================================================

# -------------------------
# TERM
# -------------------------

class TermBase(SQLModel):
    semester_name: str
    academic_year: int = Field(ge=2020)


class TermCreate(TermBase):
    pass


class TermUpdate(SQLModel):
    semester_name: str | None = None
    academic_year: int | None = Field(default=None, ge=2020)


class Term(TermBase, table=True):
    __tablename__ = "terms"

    __table_args__ = (
        Index(
            "idx_term_chronology",
            "academic_year",
            "semester_name"
        ),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )


# -------------------------
# PROFESSOR
# -------------------------

class ProfessorBase(SQLModel):
    first_name: str | None = None
    last_name: str | None = None


class ProfessorCreate(ProfessorBase):
    pass


class ProfessorUpdate(SQLModel):
    first_name: str | None = None
    last_name: str | None = None


class Professor(ProfessorBase, table=True):
    __tablename__ = "professors"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )


# -------------------------
# LETTER GRADE ENUM
# -------------------------

class LetterGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"
    W = "W"
    I = "I"


# -------------------------
# COURSE
# -------------------------

class CourseBase(SQLModel):
    course_code: str
    title: str


class CourseCreate(CourseBase):
    term_id: uuid.UUID
    professor_id: uuid.UUID | None = None
    grade: LetterGrade | None = None


class CourseUpdate(SQLModel):
    course_code: str | None = None
    title: str | None = None
    term_id: uuid.UUID | None = None
    professor_id: uuid.UUID | None = None
    grade: LetterGrade | None = None


class Course(CourseBase, table=True):
    __tablename__ = "courses"

    __table_args__ = (
        UniqueConstraint(
            "course_code",
            "term_id",
            name="uq_course_per_term"
        ),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    term_id: uuid.UUID = Field(
        foreign_key="terms.id"
    )

    professor_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="professors.id",
        ondelete="SET NULL",
    )

    grade: LetterGrade | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(LetterGrade, name="grade_letter_enum"),
            nullable=True,
        ),
    )

    # A course can have multiple tasks
    tasks: list["CourseTask"] = Relationship(
        back_populates="course",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        },
    )


# -------------------------
# COURSE TASK
# -------------------------

class CourseTaskBase(SQLModel):
    task_title: str
    weight: float = Field(sa_type=Numeric)


class CourseTaskCreate(CourseTaskBase):
    course_id: uuid.UUID


class CourseTaskUpdate(SQLModel):
    task_title: str | None = None
    weight: float | None = None
    course_id: uuid.UUID | None = None


class CourseTask(CourseTaskBase, table=True):
    __tablename__ = "course_tasks"

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "task_title",
            name="uq_task_per_course"
        ),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    course_id: uuid.UUID = Field(
        foreign_key="courses.id"
    )

    course: "Course" = Relationship(
        back_populates="tasks"
    )


# -------------------------
# COURSE RESPONSE
# -------------------------

class CoursePublic(CourseBase):
    id: uuid.UUID
    term_id: uuid.UUID
    professor_id: uuid.UUID | None = None
    grade: LetterGrade | None = None

    tasks: list[CourseTaskBase] = Field(
        default_factory=list
    )

    # Calculates total weight dynamically
    @computed_field
    @property
    def total_allocated_weight(self) -> float:
        return sum(task.weight for task in self.tasks)


# =========================================================
# PROJECT 1 & PROJECT 2 - SHOPPING CART MODELS
# =========================================================

# Many-to-many link table
class CartItem_ShoppingCart_Link(SQLModel, table=True):
    cart_item_id: uuid.UUID = Field(
        foreign_key="cartitem.id",
        primary_key=True
    )

    shopping_cart_id: uuid.UUID = Field(
        foreign_key="shoppingcart.id",
        primary_key=True
    )


# -------------------------
# CART ITEM
# -------------------------

class CartItemBase(SQLModel):
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal
    description: str | None = Field(
        default=None,
        max_length=255
    )


class CartItemCreate(CartItemBase):
    item_id: uuid.UUID


class CartItemUpdate(SQLModel):
    quantity: int | None = Field(default=None, ge=1)
    unit_price: Decimal | None = None
    description: str | None = Field(
        default=None,
        max_length=255
    )


# Restored missing database model
class CartItem(CartItemBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    # References an existing Item
    item_id: uuid.UUID = Field(
        foreign_key="item.id"
    )

    item: Item | None = Relationship()

    # Many-to-many relationship with shopping carts
    shopping_carts: list["ShoppingCart"] = Relationship(
        back_populates="cart_items",
        link_model=CartItem_ShoppingCart_Link,
    )


class CartItemPublic(CartItemBase):
    id: uuid.UUID
    item_id: uuid.UUID


class CartItemsPublic(SQLModel):
    data: list[CartItemPublic]
    count: int


# -------------------------
# SHOPPING CART
# -------------------------

class ShoppingCartBase(SQLModel):
    session_key: str
    active: bool = True
    expires: datetime
    total: Decimal


class ShoppingCartCreate(ShoppingCartBase):
    pass


class ShoppingCartUpdate(SQLModel):
    session_key: str | None = None
    active: bool | None = None
    expires: datetime | None = None
    total: Decimal | None = None


# Only ONE ShoppingCart database class
class ShoppingCart(ShoppingCartBase, table=True):
    # Time-based UUID required for Project 2
    id: uuid.UUID = Field(
        default_factory=uuid.uuid1,
        primary_key=True
    )

    # Project 2: Identifies the owner of this cart
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE"
    )

    # Connects cart to the authenticated user
    owner: "User" = Relationship(
        back_populates="shopping_carts"
    )

    # Connects cart to its cart items
    cart_items: list[CartItem] = Relationship(
        back_populates="shopping_carts",
        link_model=CartItem_ShoppingCart_Link,
    )


class ShoppingCartPublic(ShoppingCartBase):
    id: uuid.UUID


class ShoppingCartsPublic(SQLModel):
    data: list[ShoppingCartPublic]
    count: int

