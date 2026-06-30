# LEDGR API — Split Studio (Assignment 2 Implementation)

This is the working implementation submitted for CSCI 4177/5709
Assignment 2, Part 4. It implements two endpoints from the Split
Studio feature, plus the minimum supporting authentication and group
endpoints needed to demonstrate the full workflow in Postman.

## What is implemented

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/auth/register` | POST | Create a user account (supporting) |
| `/api/v1/auth/login` | POST | Obtain a JWT access + refresh token (supporting) |
| `/api/v1/groups` | POST | Create a Split Studio group (supporting) |
| `/api/v1/groups/{group_id}` | GET | Fetch one group (supporting) |
| **`/api/v1/groups/{group_id}/expenses`** | **POST** | **Graded endpoint 1 — create a shared expense** |
| **`/api/v1/groups/{group_id}/expenses`** | **GET** | **Graded endpoint 2 — list a group's expenses** |

The two bolded rows are the endpoints required by the assignment. The
others exist only so the graded endpoints can be exercised end-to-end
with a real token and a real group, per the assignment's allowance to
"add supporting services or endpoints to enable full workflow."

## Project structure

```
ledgr-api/
├── app/
│   ├── main.py            FastAPI app, CORS, error handler, route registration
│   ├── database.py        SQLAlchemy engine/session setup
│   ├── models.py          ORM models (User, Group, Expense, etc.)
│   ├── schemas.py         Pydantic request/response schemas
│   ├── security.py        Password hashing, JWT issuing/verification, RBAC
│   └── routers/
│       ├── auth.py        /auth/register, /auth/login
│       ├── groups.py      /groups (create, get)
│       └── expenses.py    /groups/{id}/expenses (the two graded endpoints)
├── requirements.txt
├── render.yaml             Render infrastructure-as-code (optional, see below)
├── schema.sql              Standalone SQL schema + seed data dump
├── seed.py                 Script to populate demo users/group for testing
├── .env.example
└── .gitignore
```

## Running locally

Requires Python 3.10+.

```bash
cd ledgr-api
pip install -r requirements.txt
cp .env.example .env
# .env defaults to SQLite, so no database setup is required to run locally.
uvicorn app.main:app --reload
```

The API will be live at `http://127.0.0.1:8000`. Interactive Swagger
docs are at `http://127.0.0.1:8000/docs`.

To create demo data for testing:
```bash
python seed.py
```
This prints the demo users' emails and IDs and creates a group called
"Apartment 4B" with all three demo users as members. All demo accounts
use the password `Password123`.
