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

## Deploying to Render

You have two options. **Option A is recommended** since it is more
reliable for grading purposes — manual setup gives you full visibility
into each step.

### Option A — Manual setup (recommended)

1. Push this project to a new GitHub repository.
2. In the Render dashboard, click **New +** → **PostgreSQL**.
   - Name: `ledgr-db`
   - Plan: Free
   - Click **Create Database**. Wait for it to become available, then
     copy the **Internal Database URL** shown on its info page.
3. Click **New +** → **Web Service**, connect your GitHub repo.
   - Name: `ledgr-api`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Plan: Free
4. Under **Environment**, add two environment variables:
   - `DATABASE_URL` → paste the Internal Database URL from step 2
   - `JWT_SECRET_KEY` → generate one locally with:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
     and paste the output as the value.
5. Click **Create Web Service**. Render will build and deploy
   automatically. The first deploy takes a few minutes.
6. Once live, your base URL will look like:
   `https://ledgr-api-xxxx.onrender.com`
7. Run the seed script against the live database to create demo data:
   ```bash
   DATABASE_URL="<paste the EXTERNAL Database URL from Render here>" python seed.py
   ```
   Use the **External** Database URL for this step (not Internal),
   since you are running the script from your own machine, not from
   inside Render's network.

### Option B — render.yaml (Blueprint)

If you'd rather not click through the dashboard, push this repo to
GitHub (it already includes `render.yaml`) and use Render's
**New + → Blueprint** option, pointing it at your repo. Render will
read `render.yaml` and provision both the database and web service
automatically, including generating `JWT_SECRET_KEY` for you. You
still need to manually run `seed.py` against the resulting database
afterward (see step 7 above).

## Testing in Postman

A suggested request sequence to reproduce the screenshots described
in the report:

1. `POST {{base_url}}/api/v1/auth/register` — register a new user
   (or skip this and use a seeded demo account).
2. `POST {{base_url}}/api/v1/auth/login` — get back an `access_token`.
   Copy it.
3. `POST {{base_url}}/api/v1/groups` — with header
   `Authorization: Bearer <access_token>` — create a group, or use the
   seeded "Apartment 4B" group ID printed by `seed.py`.
4. `POST {{base_url}}/api/v1/groups/{group_id}/expenses` — with the
   bearer token — create an expense. Example body:
   ```json
   {
     "description": "Pizza Night",
     "total_amount": 60.92,
     "paid_by": "<a member's user_id>",
     "split_mode": "equal",
     "tax_amount": 9.14,
     "tip_amount": 9.14,
     "discount_amount": 10.00,
     "shares": [
       {"user_id": "<user_id_1>", "share_amount": 22.40},
       {"user_id": "<user_id_2>", "share_amount": 22.40},
       {"user_id": "<user_id_3>", "share_amount": 24.40}
     ]
   }
   ```
5. `GET {{base_url}}/api/v1/groups/{group_id}/expenses` — with the
   bearer token — confirm the expense you just created is returned.
   This is your proof of data persistence.
6. To capture an **auth failure** screenshot: repeat step 4 or 5 with
   no `Authorization` header, or with the header set to
   `Bearer invalid.token.here`. Expect `401 Unauthorized`.
7. To capture a **validation error** screenshot: repeat step 4 with
   `shares` summing to a value that does not match
   `total_amount + tax_amount + tip_amount - discount_amount`.
   Expect `400 Bad Request`.
8. To capture a **broken-access-control** screenshot: log in as a user
   who is NOT a member of the group, and call step 4 or 5 with their
   token. Expect `403 Forbidden`.

## Notes on scope

This implementation covers two endpoints from one feature, per the
assignment's Part 4 requirement. The complete API surface for all
three core features (Personal Ledger, Split Studio, Analytics Hub)
and every security endpoint (password reset, refresh token rotation,
RBAC for admin actions) is specified in full in the written report,
Sections 1 and 2, but not all of it is implemented in code — only what
Part 4 requires.
