from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/",
    summary="Health Check",
    description="Basic health probe to verify the API is responsive.",
    operation_id="health_check",
    tags=["Health"],
)
def health_check():
    """
    PUBLIC_INTERFACE
    Health check endpoint.

    Returns:
        JSON payload with a simple 'Healthy' message.
    """
    return {"message": "Healthy"}
