from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import UserMeResponse

router = APIRouter()

@router.get("/users/me", response_model=UserMeResponse)
async def read_user_me(current_user: dict = Depends(get_current_user)):
    """
    Get the profile of the current logged-in user, regardless of their type
    (customer, agent, or admin).
    """
    # The get_current_user dependency already fetches the user document
    # and adds the 'user_type' field. We just need to return it.
    # Pydantic will automatically handle the mapping to the UserMeResponse model.
    # We need to convert the ObjectId to a string for the 'id' field.
    current_user["id"] = str(current_user["_id"])
    return current_user