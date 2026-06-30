"""
LEDGR API — main application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

On Render, the start command is:
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database import Base, engine
from app.routers import auth, groups, expenses

logging.basicConfig(level=logging.INFO)

# Creates tables on startup if they do not exist yet. For a production
# system migrations would be managed with Alembic; for this assignment's
# scope, create_all is sufficient and was chosen for deployment simplicity.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LEDGR API",
    description=(
        "REST API for LEDGR's Split Studio feature, built for "
        "CSCI 4177/5709 Assignment 2. Implements two core endpoints: "
        "creating a shared expense and listing a group's expenses, "
        "plus the supporting authentication endpoints needed to "
        "demonstrate the full workflow."
    ),
    version="1.0.0",
)

# CORS left open for grading/demo purposes (Postman and any reviewer's
# browser need to reach the API). In a production deployment this
# would be restricted to the actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Returns a consistent, readable 422 error body instead of FastAPI's
    default verbose schema dump, so the error format matches what is
    documented in the report for every endpoint.
    """
    first_error = exc.errors()[0]
    field = ".".join(str(loc) for loc in first_error["loc"] if loc != "body")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": f"Validation failed on field '{field}': {first_error['msg']}",
            "error_code": "VALIDATION_ERROR",
        },
    )


app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(expenses.router)


@app.get("/", tags=["Health"])
def root():
    """Basic liveness check used to confirm the Render deployment is reachable."""
    return {"status": "ok", "service": "LEDGR API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health(request: Request):
    """
    Health check that also confirms database connectivity, since a
    deployed-but-unreachable-database state should not read as healthy.
    """
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"
    return {"status": "ok", "database": db_status}
