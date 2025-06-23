from app.crud import CRUDBase
from app.models.review import ReviewCreate
from pydantic import BaseModel

class ReviewUpdate(BaseModel):
    pass

class CRUDReview(CRUDBase[ReviewCreate, ReviewUpdate]):
    pass

review = CRUDReview("reviews")