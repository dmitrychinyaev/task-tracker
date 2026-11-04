from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/error")
def health_error():
    """Deliberately failing route used to verify logging and error handling."""
    raise ValueError("Test exception")
