from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.crud import crud_agent
from app.db.mongodb import get_db
from app.models.agent import AgentCreate, AgentInDB, AgentUpdate
from app.core.security import get_password_hash
from app.api.deps import get_current_active_agent
from app.services import face_verification

router = APIRouter()

@router.post("/agents/register", response_model=AgentInDB)
async def register_agent(
    agent_in: AgentCreate,
    db = Depends(get_db)
):
    """
    Create a new agent (Step 1: email, phone, password).
    """
    agent = await crud_agent.agent.get_by_email(db, email=agent_in.email)
    if agent:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    hashed_password = get_password_hash(agent_in.password)
    db_agent = {
        "email": agent_in.email, 
        "hashed_password": hashed_password,
        "phone_number": agent_in.phone_number,
    }
    created_agent = await crud_agent.agent.create(db, obj_in=db_agent)
    # Here you would trigger email and phone verification flows
    return created_agent

@router.get("/agents/me", response_model=AgentInDB)
def read_agent_me(current_agent: dict = Depends(get_current_active_agent)):
    """
    Get current agent's profile.
    """
    return current_agent

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