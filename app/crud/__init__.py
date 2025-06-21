from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

# Define custom types for Pydantic models
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[CreateSchemaType, UpdateSchemaType]):
    def __init__(self, collection_name: str):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `collection_name`: A string with the MongoDB collection name
        """
        self.collection_name = collection_name

    async def get(self, db: AsyncIOMotorDatabase, id: str) -> Optional[Dict]:
        return await db[self.collection_name].find_one({"_id": ObjectId(id)})

    async def get_multi(
        self, db: AsyncIOMotorDatabase, *, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        return await db[self.collection_name].find().skip(skip).limit(limit).to_list(length=limit)

    async def create(self, db: AsyncIOMotorDatabase, *, obj_in: CreateSchemaType) -> Dict:
        obj_in_data = jsonable_encoder(obj_in)
        result = await db[self.collection_name].insert_one(obj_in_data)
        created_record = await self.get(db, result.inserted_id)
        return created_record

    async def update(
        self, db: AsyncIOMotorDatabase, *, db_obj: Dict, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Dict:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        await db[self.collection_name].update_one(
            {"_id": db_obj["_id"]}, {"$set": update_data}
        )
        updated_record = await self.get(db, db_obj["_id"])
        return updated_record

    async def remove(self, db: AsyncIOMotorDatabase, *, id: str) -> bool:
        delete_result = await db[self.collection_name].delete_one({"_id": ObjectId(id)})
        return delete_result.deleted_count == 1