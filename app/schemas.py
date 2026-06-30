"""
Pydantic schemas used for request validation and response serialization.

Keeping these separate from the SQLAlchemy models (app/models.py) is a
deliberate security boundary: it guarantees that internal-only fields
(password_hash, token_hash) can never be accidentally returned in an
API response, because the response schemas simply do not define them.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class SplitModeEnum(str, Enum):
    equal = "equal"
    itemised = "itemised"
    exact = "exact"
    percentage = "percentage"


# ── Auth schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Group schemas ─────────────────────────────────────────────────────────

class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    member_emails: List[EmailStr] = Field(default_factory=list)


class GroupResponse(BaseModel):
    id: str
    name: str
    created_by: str
    created_at: datetime
    member_count: int

    class Config:
        from_attributes = True


# ── Expense / Split Studio schemas ────────────────────────────────────────

class ExpenseShareInput(BaseModel):
    user_id: str
    share_amount: float = Field(..., ge=0)


class ExpenseCreateRequest(BaseModel):
    """
    Request body for POST /api/v1/groups/{group_id}/expenses.

    shares must sum to total_amount + tax_amount + tip_amount -
    discount_amount. This is validated server-side (see routers/expenses.py)
    rather than trusted from the client.
    """
    description: str = Field(..., min_length=1, max_length=255)
    total_amount: float = Field(..., gt=0)
    paid_by: str
    split_mode: SplitModeEnum
    tax_amount: float = Field(default=0.0, ge=0)
    tip_amount: float = Field(default=0.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    shares: List[ExpenseShareInput] = Field(..., min_length=1)


class ExpenseShareResponse(BaseModel):
    user_id: str
    share_amount: float
    settled: bool

    class Config:
        from_attributes = True


class ExpenseResponse(BaseModel):
    id: str
    group_id: str
    description: str
    total_amount: float
    paid_by: str
    split_mode: str
    tax_amount: float
    tip_amount: float
    discount_amount: float
    created_at: datetime
    shares: List[ExpenseShareResponse]

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    group_id: str
    total_expenses: int
    expenses: List[ExpenseResponse]


# ── Error schema (used in OpenAPI docs for consistency) ───────────────────

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
