from httpx import AsyncClient
from pytest_mock import MockerFixture

async def test_create_purchase_order(
    client: AsyncClient, customer_auth_token: str, test_customer, mocker: MockerFixture
):
    # Mock external services to avoid real calls and control test outcomes
    mocker.patch("app.services.geo.get_agents_in_radius", return_value=[])
    mocker.patch("app.services.notification_service.create_and_dispatch_notification")
    
    # The test_customer fixture doesn't have location, so add it
    test_customer["location"] = {"type": "Point", "coordinates": [3.3792, 6.5244]}
    
    # We need to manually override the dependency for this single test
    # because the `current_customer` in the endpoint needs the location data
    async def get_customer_with_location():
        yield test_customer

    app.dependency_overrides[get_current_active_customer] = get_customer_with_location
    
    headers = {"Authorization": f"Bearer {customer_auth_token}"}
    order_data = {
        "product_description": "A brand new iPhone 15 Pro",
        "product_image": "http://example.com/iphone.png"
    }
    
    response = await client.post(
        f"{settings.API_V1_STR}/orders/purchase",
        headers=headers,
        json=order_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Purchase order created and agents notified."
    assert data["order"]["product_description"] == order_data["product_description"]
    
    # Clean up the override
    app.dependency_overrides.clear()