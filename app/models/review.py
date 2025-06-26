from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    author_id: str
    target_agent_id: str
    message: str
    stars: int = Field(..., ge=1, le=5)

class ReviewCreate(ReviewBase):
    pass

class ReviewInDB(ReviewBase):
    id: str = Field(..., alias="_id")
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

class ReviewUpdate(BaseModel):
    """Defines fields that can be updated for a Review."""
    message: Optional[str] = None
    stars: Optional[int] = Field(None, ge=1, le=5)