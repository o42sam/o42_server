# tests/services/test_notification_service.py

import pytest
from pytest_mock import MockerFixture
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services import notification_service

@pytest.mark.asyncio
async def test_create_and_dispatch_notification(db: AsyncIOMotorDatabase, mocker: MockerFixture):
    # Mock all external and DB-writing functions that the service calls
    mock_send_email = mocker.patch("app.services.notification_service.send_email", return_value=True)
    mock_send_sms = mocker.patch("app.services.notification_service.send_sms", return_value=True)
    mock_ws_push = mocker.patch("app.services.connection_manager.manager.send_personal_message")
    mock_crud_notif = mocker.patch("app.crud.crud_notification.notification.create")
    mock_crud_msg = mocker.patch("app.crud.crud_message.message.create")

    test_user = {
        "_id": "60d5ec49e7ef5b2d3c1a2b3c",
        "email": "notify@example.com",
        "phone_number": "+15555555555"
    }
    subject = "Test Subject"
    body = "Test message body"

    # Call the function being tested
    await notification_service.create_and_dispatch_notification(db, test_user, subject, body)

    # Assert that each mocked function was called correctly
    mock_crud_notif.assert_called_once()
    mock_send_email.assert_called_once_with(to_email=test_user["email"], subject=subject, html_content=f"<p>{body}</p>")
    mock_send_sms.assert_called_once_with(phone_number=test_user["phone_number"], message=body)
    mock_crud_msg.assert_called_once()
    mock_ws_push.assert_called_once()