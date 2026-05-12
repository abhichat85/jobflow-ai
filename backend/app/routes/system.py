from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/stats/tokens")
def get_token_stats():
    return {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
