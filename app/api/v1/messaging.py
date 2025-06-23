import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from typing import List

from app.api.deps import get_current_user, get_current_user_from_query
from app.crud import crud_message, crud_customer, crud_agent
from app.db.mongodb import get_db
from app.models.message import MessageCreate, MessageInDB
from app.services.connection_manager import manager
from fastapi.encoders import jsonable_encoder


router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db=Depends(get_db),

    user: dict = Depends(get_current_user_from_query) 
):
    """
    The main WebSocket endpoint for real-time P2P messaging.
    """
    user_id = str(user["_id"])
    await manager.connect(user_id, websocket)

    try:
        while True:

            data = await websocket.receive_json()
            

            if "receiver_id" not in data or "encrypted_content" not in data:
                await manager.send_personal_message({"error": "Invalid payload"}, user_id)
                continue

            receiver_id = data["receiver_id"]
            

            

            message_in = MessageCreate(
                sender_id=user_id,
                receiver_id=receiver_id,
                encrypted_content=data["encrypted_content"]
            )


            created_message = await crud_message.message.create(db, obj_in=message_in)
            message_data = jsonable_encoder(created_message)


            await manager.send_personal_message(message_data, receiver_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"Error in WebSocket for user {user_id}: {e}")
        manager.disconnect(user_id)




@router.post("/messages/send", response_model=MessageInDB)
async def send_message_rest(
    message_in: MessageCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message via REST. The message will be stored and pushed
    to the receiver via WebSocket if they are online.
    """
    message_in.sender_id = str(current_user["_id"])
    

    created_message = await crud_message.message.create(db, obj_in=message_in)
    message_data = jsonable_encoder(created_message)


    await manager.send_personal_message(message_data, message_in.receiver_id)

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