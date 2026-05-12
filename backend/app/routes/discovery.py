from fastapi import APIRouter

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.post("/run")
def run_discovery():
    return {"status": "not_implemented", "message": "Bulk discovery requires job board adapters — use manual job entry for MVP"}
