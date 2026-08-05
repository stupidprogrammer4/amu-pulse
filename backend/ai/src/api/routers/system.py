from fastapi import APIRouter

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    """
    Desc: Report that the process is up, for container health checks.
    Returns:
        return (dict[str, str]): A fixed liveness payload.
    """
    payload = {"status": "ok"}
    return payload
