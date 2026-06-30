"""
SQLAlchemy ORM models.

This file defines the data model for the Split Studio feature plus the
security-related entities (User, RefreshToken) needed to support the
two implemented endpoints. The full LEDGR schema also includes
Personal Ledger and Analytics Hub tables; those are described in the
report's ERD but are not implemented here, since Assignment 2 only
requires two working endpoints from one feature.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, Enum, Boolean, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SplitMode(str, enum.Enum):
    equal = "equal"
    itemised = "itemised"
    exact = "exact"
    percentage = "percentage"


class UserRole(str, enum.Enum):
    member = "member"
    admin = "admin"


class User(Base):
    """
    Minimal user record. In the full LEDGR system this table also holds
    profile fields (see Personal Ledger ERD in the report). Only the
    columns needed for authentication and group membership are modeled
    here.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.member, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("GroupMember", back_populates="user")


class Group(Base):
    """A Split Studio group, e.g. 'Apartment 4B' or 'Italy Trip 2026'."""
    __tablename__ = "groups"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """Join table between User and Group. Tracks per-group role (admin vs member)."""
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=gen_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_group_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Expense(Base):
    """
    A shared expense recorded inside a group. paid_by references the
    user who fronted the money; the split among participants is stored
    in ExpenseShare rows.
    """
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=gen_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    description = Column(String(255), nullable=False)
    total_amount = Column(Float, nullable=False)
    paid_by = Column(String, ForeignKey("users.id"), nullable=False)
    split_mode = Column(Enum(SplitMode), default=SplitMode.equal, nullable=False)
    tax_amount = Column(Float, default=0.0)
    tip_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="expenses")
    shares = relationship("ExpenseShare", back_populates="expense", cascade="all, delete-orphan")


class ExpenseShare(Base):
    """Each participant's computed share of a given expense."""
    __tablename__ = "expense_shares"

    id = Column(String, primary_key=True, default=gen_uuid)
    expense_id = Column(String, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    share_amount = Column(Float, nullable=False)
    settled = Column(Boolean, default=False)

    expense = relationship("Expense", back_populates="shares")


class RefreshToken(Base):
    """
    Stores issued refresh tokens so they can be revoked (logout, password
    reset). Only the hash of the token is stored, never the raw value.
    """
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
