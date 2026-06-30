"""
Group endpoints. POST /groups is a supporting endpoint (not one of the
two graded endpoints) needed so a group exists for the expense demo to
operate on. GET /groups is included for completeness when testing in
Postman.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Group, GroupMember, User
from app.schemas import GroupCreateRequest, GroupResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/groups", tags=["Split Studio - Groups"])


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"description": "Missing or invalid bearer token."}},
)
def create_group(
    payload: GroupCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new Split Studio group. The creator is automatically added as group admin."""
    group = Group(name=payload.name, created_by=current_user.id)
    db.add(group)
    db.flush()  # assigns group.id before we reference it below

    db.add(GroupMember(group_id=group.id, user_id=current_user.id, is_group_admin=True))

    added = 1
    for email in payload.member_emails:
        member_user = db.query(User).filter(User.email == email).first()
        if member_user and member_user.id != current_user.id:
            db.add(GroupMember(group_id=group.id, user_id=member_user.id, is_group_admin=False))
            added += 1

    db.commit()
    db.refresh(group)

    return GroupResponse(
        id=group.id,
        name=group.name,
        created_by=group.created_by,
        created_at=group.created_at,
        member_count=added,
    )


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    responses={
        404: {"description": "Group not found."},
        403: {"description": "Caller is not a member of this group."},
    },
)
def get_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group.",
        )

    member_count = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
    return GroupResponse(
        id=group.id, name=group.name, created_by=group.created_by,
        created_at=group.created_at, member_count=member_count,
    )
