"""
Split Studio expense endpoints.

These are the two endpoints implemented and deployed for Assignment 2
Part 4:

    POST /api/v1/groups/{group_id}/expenses   - create a shared expense
    GET  /api/v1/groups/{group_id}/expenses   - list a group's expenses

Both endpoints require a valid bearer token (get_current_user) and
both verify that the caller is a member of the group before allowing
access — this is the broken-access-control mitigation referenced in
Section 2 of the report. A user who is authenticated but not a member
of group X cannot read or write expenses for group X, even though
they could read/write expenses for groups they do belong to.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Group, GroupMember, Expense, ExpenseShare, User
from app.schemas import ExpenseCreateRequest, ExpenseResponse, ExpenseListResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/groups", tags=["Split Studio - Expenses"])


def _assert_group_membership(db: Session, group_id: str, user_id: str) -> Group:
    """Shared helper: confirms the group exists and the caller belongs to it."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group and cannot access its expenses.",
        )
    return group


@router.post(
    "/{group_id}/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Share amounts do not reconcile with the expense total."},
        401: {"description": "Missing or invalid bearer token."},
        403: {"description": "Caller is not a member of this group."},
        404: {"description": "Group not found."},
        422: {"description": "Request body failed schema validation."},
    },
)
def create_expense(
    group_id: str,
    payload: ExpenseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record a shared expense in a group and persist each participant's
    computed share.

    Server-side reconciliation: the sum of all share_amount values
    submitted by the client must equal
        total_amount + tax_amount + tip_amount - discount_amount
    within a one-cent tolerance for floating point rounding. This
    value is never trusted from the client alone — if the frontend
    sends a split that does not add up (whether from a bug or a
    tampered request), the API rejects it with 400 rather than
    silently persisting an inconsistent ledger entry.
    """
    _assert_group_membership(db, group_id, current_user.id)

    expected_total = (
        payload.total_amount + payload.tax_amount + payload.tip_amount - payload.discount_amount
    )
    submitted_total = sum(share.share_amount for share in payload.shares)

    if abs(expected_total - submitted_total) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Share amounts sum to {submitted_total:.2f}, which does not match "
                f"the expected total of {expected_total:.2f} "
                f"(total + tax + tip - discount)."
            ),
        )

    # Confirm every referenced user is actually a member of this group.
    member_ids = {
        m.user_id for m in db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    }
    for share in payload.shares:
        if share.user_id not in member_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {share.user_id} is not a member of this group and cannot be assigned a share.",
            )

    expense = Expense(
        group_id=group_id,
        description=payload.description,
        total_amount=payload.total_amount,
        paid_by=payload.paid_by,
        split_mode=payload.split_mode.value,
        tax_amount=payload.tax_amount,
        tip_amount=payload.tip_amount,
        discount_amount=payload.discount_amount,
    )
    db.add(expense)
    db.flush()

    for share in payload.shares:
        db.add(ExpenseShare(
            expense_id=expense.id,
            user_id=share.user_id,
            share_amount=share.share_amount,
        ))

    db.commit()
    db.refresh(expense)
    return expense


@router.get(
    "/{group_id}/expenses",
    response_model=ExpenseListResponse,
    responses={
        401: {"description": "Missing or invalid bearer token."},
        403: {"description": "Caller is not a member of this group."},
        404: {"description": "Group not found."},
    },
)
def list_expenses(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return every expense recorded in a group, most recent first, with each expense's per-person shares."""
    _assert_group_membership(db, group_id, current_user.id)

    expenses = (
        db.query(Expense)
        .options(joinedload(Expense.shares))
        .filter(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc())
        .all()
    )

    return ExpenseListResponse(
        group_id=group_id,
        total_expenses=len(expenses),
        expenses=expenses,
    )
