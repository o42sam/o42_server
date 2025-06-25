from pydantic import BaseModel, Field
from datetime import date

class DailyAnalyticsSnapshot(BaseModel):
    id: str = Field(..., alias="_id")
    date: date
    
    # User Metrics
    total_customers: int
    total_agents: int
    new_customers_today: int
    new_agents_today: int
    dau_customers: int # Daily Active Users
    dau_agents: int
    
    # Order Metrics
    new_purchase_orders_today: int
    new_sale_orders_today: int
    orders_fulfilled_today: int
    
    # Financial Metrics
    total_transaction_value_today: float # Gross Merchandise Value (GMV)