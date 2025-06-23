import asyncio
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from typing import List

from app.api.deps import get_current_user, get_current_user_from_query
from app.crud import crud_message
from app.db.mongodb import get_db
from app.db.redis_client import get_redis
from app.models.message import MessageCreate, MessageInDB

router = APIRouter()

# --- WebSocket Listener and Publisher ---

async def redis_listener(websocket: WebSocket, user_id: str):
    """
    Listens for messages on the user's dedicated Redis channel and
    forwards them to the user's WebSocket.
    """
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"channel:{user_id}"
    await pubsub.subscribe(channel)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message and message["type"] == "message":
                # Forward the message data received from Redis to the client's WebSocket
                await websocket.send_text(message["data"].decode('utf-8'))
    except Exception as e:
        print(f"Listener error for {user_id}: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        print(f"Unsubscribed listener for {user_id}")


async def websocket_publisher(websocket: WebSocket, user_id: str):
    """
    Listens for messages from the client's WebSocket, persists them,
    and publishes them to the recipient's Redis channel.
    """
    redis = await get_redis()
    db = await anext(get_db()) # Get a DB session for this task

    try:
        while True:
            data = await websocket.receive_json()
            
            if "receiver_id" not in data or "encrypted_content" not in data:
                continue # Ignore invalid payloads

            message_in = MessageCreate(
                sender_id=user_id,
                receiver_id=data["receiver_id"],
                encrypted_content=data["encrypted_content"]
            )
            
            # 1. Persist the message to MongoDB
            created_message = await crud_message.message.create(db, obj_in=message_in)
            message_data = jsonable_encoder(created_message)

            # 2. Publish to the recipient's channel
            recipient_channel = f"channel:{data['receiver_id']}"
            await redis.publish(recipient_channel, json.dumps(message_data))
    except WebSocketDisconnect:
        # This is expected when the client disconnects, no action needed here.
        pass
    except Exception as e:
        print(f"Publisher error for {user_id}: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: dict = Depends(get_current_user_from_query) 
):
    """
    The main WebSocket endpoint for real-time P2P messaging.
    It establishes the connection and runs listener/publisher tasks concurrently.
    """
    user_id = str(user["_id"])
    await websocket.accept()
    
    # Create two concurrent tasks: one for listening to Redis and one for listening to the WebSocket
    listener_task = asyncio.create_task(redis_listener(websocket, user_id))
    publisher_task = asyncio.create_task(websocket_publisher(websocket, user_id))
    
    # Wait for either task to finish (which happens on disconnect or error)
    done, pending = await asyncio.wait(
        [listener_task, publisher_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Clean up pending tasks to prevent them from running forever
    for task in pending:
        task.cancel()
    
    print(f"WebSocket connection closed for user {user_id}")


# --- REST Endpoints for Message History and Offline Sending ---

@router.post("/messages/send", response_model=MessageInDB)
async def send_message_rest(
    message_in: MessageCreate,
    db=Depends(get_db),
    redis=Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message via REST. The message will be stored and published
    to Redis for real-time delivery if the receiver is online.
    """
    message_in.sender_id = str(current_user["_id"])
    
    # 1. Save the message to the database
    created_message = await crud_message.message.create(db, obj_in=message_in)
    message_data = jsonable_encoder(created_message)

    # 2. Publish to the recipient's channel on Redis
    recipient_channel = f"channel:{message_in.receiver_id}"
    await redis.publish(recipient_channel, json.dumps(message_data))

    return created_message


@router.get("/messages/inbox/{contact_id}", response_model=List[MessageInDB])
async def get_message_history(
    contact_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve message history between the current user and a specific contact.
    """
    user_id = str(current_user["_id"])
    
    query = {
        "$or": [
            {"sender_id": user_id, "receiver_id": contact_id},
            {"sender_id": contact_id, "receiver_id": user_id},
        ]
    }
    
    messages = await db.messages.find(query).sort("created", 1).to_list(length=None)
    return messages