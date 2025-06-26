from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.crud import agent as crud_agent # <-- Use aliased import
from app.db.mongodb import get_db
# Import the new response model
from app.models.agent import AgentCreate, AgentInDB, AgentUpdate, AgentRegisterOut
from app.core.security import get_password_hash
from app.api.deps import get_current_active_agent, get_current_user
from app.services import face_verification

router = APIRouter()

@router.post("/agents/register", response_model=AgentRegisterOut)
async def register_agent(
    agent_in: AgentCreate,
    db = Depends(get_db)
):
    agent = await crud_agent.get_by_email(db, email=agent_in.email)
    if agent:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    hashed_password = get_password_hash(agent_in.password)
    db_agent_data = {
        "email": agent_in.email, 
        "hashed_password": hashed_password,
        "phone_number": agent_in.phone_number,
        "isEmailVerified": False,
        "isPhoneNumberVerified": False
    }
    result = await db.agents.insert_one(db_agent_data)
    created_agent = await db.agents.find_one({"_id": result.inserted_id})
    
    return {
        "id": str(created_agent["_id"]),
        "email": created_agent["email"],
        "phone_number": created_agent["phone_number"],
        "isEmailVerified": created_agent.get("isEmailVerified", False),
        "isPhoneNumberVerified": created_agent.get("isPhoneNumberVerified", False)
    }

@router.put("/agents/me/verify-face", response_model=AgentInDB)
async def upload_face_verification_video(
    db = Depends(get_db),
    current_agent: dict = Depends(get_current_active_agent),
    video: UploadFile = File(...)
):
    """
    Upload a video for face verification. Creates the face mapping.
    """
    face_mapping = await face_verification.create_face_mapping_from_video(video)
    if not face_mapping:
        raise HTTPException(status_code=400, detail="Could not detect a face in the video.")
    
    updated_agent = await crud_agent.agent.update(
        db, db_obj=current_agent, obj_in={"face_mapping": face_mapping}
    )
    return updated_agent