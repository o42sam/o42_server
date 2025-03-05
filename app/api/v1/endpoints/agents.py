import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_db
from app.core.security import get_current_user, hash_password
from app.models.agent import Agent, AgentCreate, AgentUpdate
from app.services.face_verification import process_photo
from app.services.email import send_verification_email
from app.services.sms import send_verification_sms
from app.utils.helpers import generate_verification_code
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Agent)
async def create_agent(
    agent_data: AgentCreate = Depends(),
    id_photo: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_db)
):
    logger.info(f"Creating agent with email: {agent_data.email}")
    # Check if email or phone exists
    if await db.o42.agents.find_one({"email": agent_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await db.o42.agents.find_one({"phone_number": agent_data.phone_number}):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Hash password
    hashed_password = hash_password(agent_data.password)
    agent_dict = agent_data.dict(exclude={"password"})
    agent_dict["password"] = hashed_password
    agent_dict["location"] = {"type": "Point", "coordinates": agent_data.location}

    # Save photo to local storage (replace with S3 in prod)
    photo_path = f"uploads/{id_photo.filename}"
    with open(photo_path, "wb") as f:
        f.write(await id_photo.read())
    agent_dict["personal_identification"]["id_photo"] = photo_path

    # Insert agent
    result = await db.o42.agents.insert_one(agent_dict)
    agent_id = str(result.inserted_id)
    agent_dict["id"] = agent_id

    # Generate and store verification codes
    email_code = generate_verification_code()
    phone_code = generate_verification_code()
    await db.o42.verification_codes.insert_many([
        {"user_id": agent_id, "code": email_code, "type": "email", "created_at": agent_dict["created_at"], "expires_at": agent_dict["created_at"] + timedelta(minutes=15)},
        {"user_id": agent_id, "code": phone_code, "type": "phone", "created_at": agent_dict["created_at"], "expires_at": agent_dict["created_at"] + timedelta(minutes=15)}
    ])

    # Send verification codes
    await send_verification_email(agent_data.email, email_code)
    await send_verification_sms(agent_data.phone_number, phone_code)

    # Process photo asynchronously
    process_photo.delay(agent_id, photo_path)

    return Agent(**agent_dict)

@router.get("/{agent_id}", response_model=Agent)
async def read_agent(agent_id: str, db: AsyncIOMotorClient = Depends(get_db), current_user: Agent = Depends(get_current_user)):
    logger.info(f"Fetching agent: {agent_id}")
    agent = await db.o42.agents.find_one({"_id": ObjectId(agent_id)})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent["id"] = str(agent["_id"])
    return Agent(**agent)

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    db: AsyncIOMotorClient = Depends(get_db),
    current_user: Agent = Depends(get_current_user)
):
    logger.info(f"Updating agent: {agent_id}")
    if str(current_user.id) != agent_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    update_data = {k: v for k, v in agent_update.dict(exclude_unset=True).items() if v is not None}
    if "location" in update_data:
        update_data["location"] = {"type": "Point", "coordinates": update_data["location"]}
    update_data["updated_at"] = datetime.utcnow()
    result = await db.o42.agents.update_one({"_id": ObjectId(agent_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found or no changes made")
    agent = await db.o42.agents.find_one({"_id": ObjectId(agent_id)})
    agent["id"] = str(agent["_id"])
    return Agent(**agent)

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, db: AsyncIOMotorClient = Depends(get_db), current_user: Agent = Depends(get_current_user)):
    logger.info(f"Deleting agent: {agent_id}")
    if str(current_user.id) != agent_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.o42.agents.delete_one({"_id": ObjectId(agent_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")