# tests/services/test_image_generation.py

import pytest
from pytest_mock import MockerFixture
from app.services import image_generation

@pytest.mark.asyncio
async def test_generate_product_image_from_prompt(mocker: MockerFixture):
    # Mock all the Google Cloud dependencies
    mocker.patch("app.services.image_generation.vertexai.init")
    mock_image_model = mocker.MagicMock()
    mock_generated_image = mocker.MagicMock()
    mock_generated_image._image_bytes = b"fakeimagedata"
    mock_image_model.generate_images.return_value.images = [mock_generated_image]
    mocker.patch("app.services.image_generation.ImageGenerationModel.from_pretrained", return_value=mock_image_model)
    mock_upload = mocker.patch("app.services.image_generation._upload_to_gcs", return_value="http://fake.url/image.png")

    # Test with a valid prompt
    prompt = "A red shoe"
    result_url = await image_generation.generate_product_image_from_prompt(prompt)

    assert result_url == "http://fake.url/image.png"
    mock_upload.assert_called_once_with(b"fakeimagedata", mocker.ANY) # Check if upload was called with bytes

    # Test with a forbidden prompt
    with pytest.raises(ValueError, match="The provided description contains terms that are not allowed."):
        await image_generation.generate_product_image_from_prompt("A picture of a person")