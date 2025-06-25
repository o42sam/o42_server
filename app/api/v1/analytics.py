from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List
from datetime import datetime, timedelta, date

from app.api.deps import get_current_admin
from app.db.mongodb import get_db
from app.models.analytics import DailyAnalyticsSnapshot

router = APIRouter()

async def _calculate_metrics_for_period(db, start_date: datetime, end_date: datetime):
    """Helper function to calculate metrics for a given time window."""
    # User Metrics
    total_customers = await db.customers.count_documents({})
    total_agents = await db.agents.count_documents({})
    new_customers = await db.customers.count_documents({"created": {"$gte": start_date, "$lt": end_date}})
    new_agents = await db.agents.count_documents({"created": {"$gte": start_date, "$lt": end_date}})
    dau_customers = await db.customers.count_documents({"last_login": {"$gte": start_date, "$lt": end_date}})
    dau_agents = await db.agents.count_documents({"last_login": {"$gte": start_date, "$lt": end_date}})
    
    # Order Metrics
    new_po = await db.purchase_orders.count_documents({"created": {"$gte": start_date, "$lt": end_date}})
    new_so = await db.sale_orders.count_documents({"created": {"$gte": start_date, "$lt": end_date}})
    
    # Financials & Fulfillment
    # Sum the 'amount' field from all transactions within the period
    pipeline = [
        {"$match": {"created": {"$gte": start_date, "$lt": end_date}}},
        {"$group": {"_id": None, "total_value": {"$sum": "$amount"}}}
    ]
    total_value_cursor = db.transactions.aggregate(pipeline)
    total_value_result = await total_value_cursor.to_list(length=1)
    total_gmv = total_value_result[0]['total_value'] if total_value_result else 0
    
    fulfilled_orders = await db.transactions.count_documents({"created": {"$gte": start_date, "$lt": end_date}})
    
    return {
        "date": start_date.date(),
        "total_customers": total_customers, "total_agents": total_agents,
        "new_customers_today": new_customers, "new_agents_today": new_agents,
        "dau_customers": dau_customers, "dau_agents": dau_agents,
        "new_purchase_orders_today": new_po, "new_sale_orders_today": new_so,
        "orders_fulfilled_today": fulfilled_orders,
        "total_transaction_value_today": total_gmv
    }

@router.get("/analytics/current", response_model=DailyAnalyticsSnapshot)
async def get_current_analytics(
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get real-time analytics calculated for the current day (since midnight UTC).
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    now = datetime.utcnow()
    metrics = await _calculate_metrics_for_period(db, today_start, now)
    # Add a dummy ID for Pydantic validation
    metrics["_id"] = str(int(datetime.utcnow().timestamp()))
    return metrics

@router.get("/analytics/historical", response_model=List[DailyAnalyticsSnapshot])
async def get_historical_analytics(
    db=Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get all previously generated daily analytics snapshots.
    Perfect for populating a time-series graph.
    """
    snapshots = await db.analytics.find().sort("date", -1).to_list(length=365)
    return snapshots

@router.post("/analytics/snapshot", status_code=202)
async def create_daily_analytics_snapshot(
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Triggers a background task to calculate analytics for the PREVIOUS full day
    and save it to the database. Can be called by a cron job once per day.
    """
    async def do_snapshot():
        db = await anext(get_db()) # Get a new DB session for the background task
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        # Check if a snapshot for yesterday already exists
        if await db.analytics.find_one({"date": yesterday_start.date()}):
            print(f"Analytics snapshot for {yesterday_start.date()} already exists.")
            return

        metrics = await _calculate_metrics_for_period(db, yesterday_start, today_start)
        await db.analytics.insert_one(metrics)
        print(f"Successfully created analytics snapshot for {yesterday_start.date()}")

    background_tasks.add_task(do_snapshot)
    return {"message": "Daily analytics snapshot generation has been triggered in the background."}