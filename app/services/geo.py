from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.models.agent import AgentSubscriptionTier

async def get_agents_in_radius(db: AsyncIOMotorDatabase, longitude: float, latitude: float) -> List[Dict]:
    """
    Finds agents within a predefined radius from a location.
    Sorts them by subscription tier (Tycoon > Runner > Starter) and then by distance.
    """

    coordinates = [longitude, latitude]
    radius_in_meters = settings.AGENT_LINKING_RADIUS_KM * 1000

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": coordinates},
                "distanceField": "dist.calculated",
                "maxDistance": radius_in_meters,
                "spherical": True,
            }
        },

        {
            "$addFields": {
                "tierSortOrder": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$subscription_tier", AgentSubscriptionTier.tycoon]}, "then": 1},
                            {"case": {"$eq": ["$subscription_tier", AgentSubscriptionTier.runner]}, "then": 2},
                            {"case": {"$eq": ["$subscription_tier", AgentSubscriptionTier.starter]}, "then": 3},
                        ],
                        "default": 4,
                    }
                }
            }
        },

        {"$sort": {"tierSortOrder": 1, "dist.calculated": 1}},
    ]

    agents_cursor = db.agents.aggregate(pipeline)
    return await agents_cursor.to_list(length=None)