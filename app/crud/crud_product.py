from app.crud import CRUDBase
from app.models.product import ProductCreate, ProductUpdate

class CRUDProduct(CRUDBase[ProductCreate, ProductUpdate]):
    pass

product = CRUDProduct("products")