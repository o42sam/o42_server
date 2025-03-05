import logging
import face_recognition
from celery import Celery
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.database import get_db
from bson import ObjectId

celery = Celery('o42', broker='redis://localhost:6379/0')
logger = logging.getLogger(__name__)

@celery.task
def process_photo(agent_id: str, photo_path: str):
    logger.info(f"Processing photo for agent: {agent_id}")
    image = face_recognition.load_image_file(photo_path)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) != 1:
        logger.error(f"Invalid number of faces detected: {len(encodings)}")
        return
    encoding = encodings[0].tolist()
    db = AsyncIOMotorClient(settings.MONGODB_URI).get_default_database()
    await db.o42.agents.update_one({"_id": ObjectId(agent_id)}, {"$set": {"face_encoding": encoding}})

async def verify_face(agent_id: str, photo_path: str) -> bool:
    logger.info(f"Verifying face for agent: {agent_id}")
    db = AsyncIOMotorClient(settings.MONGODB_URI).get_default_database()
    agent = await db.o42.agents.find_one({"_id": ObjectId(agent_id)})
    if not agent or "face_encoding" not in agent:
        return False
    stored_encoding = agent["face_encoding"]
    image = face_recognition.load_image_file(photo_path)
    new_encodings = face_recognition.face_encodings(image)
    if len(new_encodings) != 1:
        return False
    new_encoding = new_encodings[0]
    match = face_recognition.compare_faces([stored_encoding], new_encoding, tolerance=0.6)[0]
    return match