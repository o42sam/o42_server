# tests/services/test_geo_service.py

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services import geo
from app.models.agent import AgentSubscriptionTier

@pytest.mark.asyncio
async def test_get_agents_in_radius(db: AsyncIOMotorDatabase):
    # This is an integration test with a real (test) database
    await db.agents.create_index([("location", "2dsphere")])

    # Insert mock agents
    agents_to_insert = [
        # In radius (< 10km), should be returned
        {"_id": "agent_1", "location": {"type": "Point", "coordinates": [3.38, 6.52]}, "subscription_tier": AgentSubscriptionTier.runner}, # ~0.1km away
        {"_id": "agent_2", "location": {"type": "Point", "coordinates": [3.40, 6.55]}, "subscription_tier": AgentSubscriptionTier.tycoon}, # ~3.7km away
        # Out of radius (> 10km), should NOT be returned
        {"_id": "agent_3", "location": {"type": "Point", "coordinates": [3.50, 6.60]}, "subscription_tier": AgentSubscriptionTier.starter}, # ~15km away
        # In radius, but lower tier than agent_1
        {"_id": "agent_4", "location": {"type": "Point", "coordinates": [3.37, 6.52]}, "subscription_tier": AgentSubscriptionTier.starter}, # ~0.1km away
    ]
    await db.agents.insert_many(agents_to_insert)

    # Center point for the search (Lagos)
    longitude, latitude = 3.3792, 6.5244

    # Call the service
    nearby_agents = await geo.get_agents_in_radius(db, longitude, latitude)

    # Assertions
    assert len(nearby_agents) == 3
    
    nearby_agent_ids = [agent["_id"] for agent in nearby_agents]
    assert "agent_1" in nearby_agent_ids
    assert "agent_2" in nearby_agent_ids
    assert "agent_4" in nearby_agent_ids
    assert "agent_3" not in nearby_agent_ids
    
    # Assert correct sorting: Tycoon > Runner > Starter
    assert nearby_agent_ids[0] == "agent_2" # Tycoon is first
    assert nearby_agent_ids[1] == "agent_1" # Runner is second
    assert nearby_agent_ids[2] == "agent_4" # Starter is last