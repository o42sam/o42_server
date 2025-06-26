from app.crud import CRUDBase
from app.models.review import ReviewCreate, ReviewUpdate

class CRUDReview(CRUDBase[ReviewCreate, ReviewUpdate]):
    pass

review = CRUDReview("reviews")