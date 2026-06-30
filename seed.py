"""
Seed script — creates two demo users and a group so you have real data
to test against in Postman without manually registering accounts every
time you redeploy.

Run locally with:
    python seed.py

Run against the deployed Render database by setting DATABASE_URL to
the Render Postgres connection string before running this script, e.g.:
    DATABASE_URL="postgresql://..." python seed.py
"""

from app.database import SessionLocal, Base, engine
from app.models import User, UserRole, Group, GroupMember
from app.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

demo_users = [
    {"full_name": "Het Soni", "email": "het.soni@dal.ca", "password": "Password123"},
    {"full_name": "Vijay Puttarevaiah", "email": "vijay.p@dal.ca", "password": "Password123"},
    {"full_name": "Jake Nurilov", "email": "rn423978@dal.ca", "password": "Password123"},
]

created_users = []
for u in demo_users:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if existing:
        created_users.append(existing)
        continue
    user = User(
        full_name=u["full_name"],
        email=u["email"],
        password_hash=hash_password(u["password"]),
        role=UserRole.member,
    )
    db.add(user)
    db.flush()
    created_users.append(user)

db.commit()

existing_group = db.query(Group).filter(Group.name == "Apartment 4B").first()
if not existing_group:
    group = Group(name="Apartment 4B", created_by=created_users[0].id)
    db.add(group)
    db.flush()
    for i, user in enumerate(created_users):
        db.add(GroupMember(group_id=group.id, user_id=user.id, is_group_admin=(i == 0)))
    db.commit()
    print(f"Created group 'Apartment 4B' with id: {group.id}")
else:
    print(f"Group 'Apartment 4B' already exists with id: {existing_group.id}")

print("\nDemo accounts (all use password: Password123):")
for u in created_users:
    print(f"  {u.email}  ->  user_id: {u.id}")

db.close()
