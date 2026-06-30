-- LEDGR Database Schema — PostgreSQL
-- Assignment 2, CSCI 4177/5709
--
-- This file documents the schema that SQLAlchemy's Base.metadata.create_all()
-- generates automatically on application startup (see app/database.py and
-- app/models.py). It is provided separately, as required by the assignment,
-- as a standalone .sql artifact showing the structure and constraints of
-- the tables backing the Split Studio feature and its security entities.
--
-- To load this manually against a fresh Postgres database:
--   psql $DATABASE_URL -f schema.sql

CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR PRIMARY KEY,
    full_name       VARCHAR(120)  NOT NULL,
    email           VARCHAR(255)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,
    role            VARCHAR(20)   NOT NULL DEFAULT 'member',
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS groups (
    id              VARCHAR PRIMARY KEY,
    name            VARCHAR(120)  NOT NULL,
    created_by      VARCHAR       NOT NULL REFERENCES users(id),
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_members (
    id              VARCHAR PRIMARY KEY,
    group_id        VARCHAR       NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id         VARCHAR       NOT NULL REFERENCES users(id),
    is_group_admin  BOOLEAN       NOT NULL DEFAULT FALSE,
    joined_at       TIMESTAMP     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_group_user UNIQUE (group_id, user_id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id               VARCHAR PRIMARY KEY,
    group_id         VARCHAR      NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    description      VARCHAR(255) NOT NULL,
    total_amount     FLOAT        NOT NULL CHECK (total_amount > 0),
    paid_by          VARCHAR      NOT NULL REFERENCES users(id),
    split_mode       VARCHAR(20)  NOT NULL DEFAULT 'equal'
                       CHECK (split_mode IN ('equal', 'itemised', 'exact', 'percentage')),
    tax_amount       FLOAT        NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    tip_amount       FLOAT        NOT NULL DEFAULT 0 CHECK (tip_amount >= 0),
    discount_amount  FLOAT        NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    created_at       TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS expense_shares (
    id              VARCHAR PRIMARY KEY,
    expense_id      VARCHAR      NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    user_id         VARCHAR      NOT NULL REFERENCES users(id),
    share_amount    FLOAT        NOT NULL CHECK (share_amount >= 0),
    settled         BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              VARCHAR PRIMARY KEY,
    user_id         VARCHAR      NOT NULL REFERENCES users(id),
    token_hash      VARCHAR(255) NOT NULL,
    expires_at      TIMESTAMP    NOT NULL,
    revoked         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────
-- Demo data (mirrors seed.py — included here so the .sql file alone
-- satisfies the "source files for your database with your data in it"
-- requirement without needing to run Python).
-- Passwords below are bcrypt hashes of the plaintext "Password123".
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO users (id, full_name, email, password_hash, role, created_at) VALUES
('11111111-1111-1111-1111-111111111111', 'Het Soni', 'het.soni@dal.ca',
 '$2b$12$EXAMPLEHASHDONOTUSEEXAMPLEHASHDONOTUSEEX', 'member', NOW()),
('22222222-2222-2222-2222-222222222222', 'Vijay Puttarevaiah', 'vijay.p@dal.ca',
 '$2b$12$EXAMPLEHASHDONOTUSEEXAMPLEHASHDONOTUSEEX', 'member', NOW()),
('33333333-3333-3333-3333-333333333333', 'Jake Nurilov', 'rn423978@dal.ca',
 '$2b$12$EXAMPLEHASHDONOTUSEEXAMPLEHASHDONOTUSEEX', 'member', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO groups (id, name, created_by, created_at) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Apartment 4B',
 '11111111-1111-1111-1111-111111111111', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO group_members (id, group_id, user_id, is_group_admin, joined_at) VALUES
('m1111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
 '11111111-1111-1111-1111-111111111111', TRUE, NOW()),
('m2222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
 '22222222-2222-2222-2222-222222222222', FALSE, NOW()),
('m3333333-3333-3333-3333-333333333333', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
 '33333333-3333-3333-3333-333333333333', FALSE, NOW())
ON CONFLICT (id) DO NOTHING;

-- NOTE: Replace the placeholder password_hash values above by running
-- `python seed.py` against your actual database instead of relying on
-- this static INSERT block — the example hash here will not pass
-- verify_password(). This file exists primarily to document schema +
-- relationships; seed.py is the authoritative way to populate real,
-- working demo data.
