import logging
from celery import Celery
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.email import send_verification_email
from app.services.sms import send_verification_sms
from sentence_transformers import SentenceTransformer, util
from bson import ObjectId

celery = Celery('o42', broker='redis://localhost:6379/0')
logger = logging.getLogger(__name__)
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

@celery.task
def match_order(order_id: str):
    logger.info(f"Matching order: {order_id}")
    db = AsyncIOMotorClient(settings.MONGODB_URI).get_default_database()
    order = await db.o42.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return

    description = f"{order['product']['description']} {order['order_description']}"
    embedding = model.encode(description)
    opposite_type = "purchase" if order["type"] == "sale" else "sale"
    cursor = db.o42.orders.find({"type": opposite_type})
    matches = []
    async for counter_order in cursor:
        counter_desc = f"{counter_order['product']['description']} {counter_order['order_description']}"
        counter_embedding = model.encode(counter_desc)
        similarity = util.cos_sim(embedding, counter_embedding).item()
        matches.append((str(counter_order["_id"]), similarity))
    matches.sort(key=lambda x: x[1], reverse=True)
    top_matches = [match[0] for match in matches[:5]]
    await db.o42.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"matching_orders": top_matches}})

    # Notify agents
    location = order["order_location"]
    distance = 5  # km
    agents = []
    while len(agents) < 5 and distance <= 55:
        agents = await db.o42.agents.find({
            "location": {
                "$near": {
                    "$geometry": location,
                    "$maxDistance": distance * 1000  # Convert km to meters
                }
            }
        }).to_list(length=5)
        distance += 10
    for agent in agents[:5]:
        msg = f"New {order['type']} order: {order['product']['description']} at {location['coordinates']}"
        await send_verification_email(agent["email"], msg)
        send_verification_sms(agent["phone_number"], msg)