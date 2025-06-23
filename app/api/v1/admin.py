from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional

from app.api.deps import get_current_admin
from app.db.mongodb import get_db
from app.models.admin import AdminCreate, AdminInDB
from app.crud import admin as crud_admin, customer as crud_customer, agent as crud_agent
from app.core.security import get_password_hash
from app.services.notification_service import create_and_dispatch_notification
from app.models.admin import AdminCreate, AdminUpdate, AdminInDB, AdminOut

router = APIRouter()

# --- Admin Management Endpoints ---

@router.post("/admin/create", response_model=AdminInDB, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_in: AdminCreate,
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Create a new administrator. Only an existing admin can do this.
    """
    if not current_admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Only super admins can create other admins.")

    if await crud_admin.get_by_email(db, email=admin_in.email):
        raise HTTPException(status_code=400, detail="Admin with this email already exists.")
    
    admin_in.password = get_password_hash(admin_in.password)
    # Convert model to dict to store hashed password correctly
    admin_to_create = {"email": admin_in.email, "full_name": admin_in.full_name, "hashed_password": admin_in.password, "is_super_admin": admin_in.is_super_admin}
    
    created_admin = await crud_admin.create(db, obj_in=admin_to_create)
    return created_admin

# ... (You would add GET, PUT, DELETE endpoints for managing admins here) ...


# --- Admin Notification Endpoint ---

@router.post("/admin/notify", status_code=status.HTTP_202_ACCEPTED)
async def notify_users(
    db=Depends(get_db),
    subject: str = Body(...),
    message: str = Body(...),
    target_user_id: Optional[str] = Body(None, description="Specific user ID (customer or agent) to notify. If null, broadcasts to the target_group."),
    target_group: Optional[str] = Body(None, description="Group to notify ('customers' or 'agents'). Used if target_user_id is null."),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Send a notification from an admin to users.
    - If target_user_id is provided, sends to that specific user.
    - If target_group ('customers' or 'agents') is provided, broadcasts to all users in that group.
    """
    if target_user_id:
        # Find the specific user (check both collections)
        user = await crud_customer.get(db, id=target_user_id) or await crud_agent.get(db, id=target_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Target user not found.")
        
        users_to_notify = [user]
        
        # Create a single notification record for the specific user
        await create_and_dispatch_notification(db, user, subject, message)

    elif target_group in ["customers", "agents"]:
        # Broadcast to a group
        if target_group == "customers":
            users_to_notify = await db.customers.find().to_list(length=None)
        else: # target_group == "agents"
            users_to_notify = await db.agents.find().to_list(length=None)

        # Create a single broadcast notification record with target_user_id as null
        # (This assumes create_and_dispatch_notification handles a null user_id for broadcast logging)
        # For simplicity now, we will just iterate and create individual notifications.
        for user in users_to_notify:
            await create_and_dispatch_notification(db, user, subject, message)
            
    else:
        raise HTTPException(status_code=400, detail="Must provide either a 'target_user_id' or a valid 'target_group' ('customers' or 'agents').")

    return {"message": "Notifications are being dispatched.", "recipient_count": len(users_to_notify)}

@router.get("/admin/all", response_model=List[AdminOut])
async def read_admins(
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Retrieve all admin users. Only accessible by other admins.
    """
    admins = await crud_admin.get_multi(db)
    return admins

@router.get("/admin/{admin_id}", response_model=AdminOut)
async def read_admin(
    admin_id: str,
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get a specific admin by their ID.
    """
    admin = await crud_admin.get(db, id=admin_id)
    if admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

@router.put("/admin/{admin_id}", response_model=AdminOut)
async def update_admin(
    admin_id: str,
    admin_in: AdminUpdate,
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Update an admin's information. Only super admins can do this.
    """
    if not current_admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Only super admins can update other admins.")

    admin_to_update = await crud_admin.get(db, id=admin_id)
    if not admin_to_update:
        raise HTTPException(status_code=404, detail="Admin to update not found.")
        
    updated_admin = await crud_admin.update(db, db_obj=admin_to_update, obj_in=admin_in)
    return updated_admin

@router.delete("/admin/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: str,
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Delete an admin user. Only super admins can do this.
    A super admin cannot delete themselves.
    """
    if not current_admin.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Only super admins can delete other admins.")

    if str(current_admin["_id"]) == admin_id:
        raise HTTPException(status_code=400, detail="Super admins cannot delete their own accounts.")
        
    admin_to_delete = await crud_admin.get(db, id=admin_id)
    if not admin_to_delete:
        raise HTTPException(status_code=404, detail="Admin to delete not found.")
    
    await crud_admin.remove(db, id=admin_id)
    return