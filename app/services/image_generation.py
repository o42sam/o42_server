# app/services/image_generation.py

import uuid
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import storage
from google.api_core import exceptions as google_exceptions
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

# --- Initialize Google Cloud Services ---
try:
    # Initialize Vertex AI
    vertexai.init(project=settings.GOOGLE_CLOUD_PROJECT, location=settings.GOOGLE_CLOUD_REGION)
    
    # Initialize Google Cloud Storage client
    storage_client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
    
    # Initialize Google Search Client
    google_search_service = build("customsearch", "v1", developerKey=settings.GOOGLE_API_KEY)

except Exception as e:
    print(f"CRITICAL: Failed to initialize Google Cloud services: {e}")
    print("Please ensure you have authenticated with 'gcloud auth application-default login'")
    storage_client = None
    google_search_service = None


# --- Safeguards against misuse ---
FORBIDDEN_PROMPT_KEYWORDS = [
    "nudity", "naked", "obscene", "violence", "hate speech",
    "self-harm", "graphic", "person", "celebrity", "portrait"
]

async def _upload_to_gcs(image_bytes: bytes, destination_blob_name: str) -> str:
    """Uploads image bytes to GCS and returns the public URL."""
    if not storage_client:
        raise Exception("Google Cloud Storage client not initialized.")
        
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(
            image_bytes,
            content_type="image/png"
        )

        # Make the blob publicly viewable
        blob.make_public()
        
        return blob.public_url
    except google_exceptions.NotFound:
        raise Exception(f"GCS bucket '{settings.GCS_BUCKET_NAME}' not found.")
    except Exception as e:
        print(f"Failed to upload to GCS: {e}")
        raise Exception("Could not save generated image to cloud storage.")


async def generate_product_image_from_prompt(prompt: str) -> str:
    """
    Generates an image using Vertex AI Gemini/Imagen, saves it to GCS, 
    and returns the public URL.
    """
    # 1. Safeguard check
    if any(keyword in prompt.lower() for keyword in FORBIDDEN_PROMPT_KEYWORDS):
        raise ValueError("The provided description contains terms that are not allowed.")

    print(f"--- GENERATING IMAGE WITH VERTEX AI FOR PROMPT: '{prompt}' ---")
    
    # 2. Instantiate the model
    # Using 'imagegeneration@006' which is a powerful Imagen 2 model on Vertex AI
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")

    # 3. Generate the image
    try:
        # Enhancing prompt for better e-commerce results
        enhanced_prompt = f"A professional, clean e-commerce product photo of: {prompt}. Centered, on a white background, without text or watermarks, hyper-realistic."
        
        response = model.generate_images(
            prompt=enhanced_prompt,
            number_of_images=1,
            aspect_ratio="1:1",  # Square images are standard for marketplaces
            safety_filter_level="block_most",
        )

        if not response.images:
            raise Exception("Image generation failed or was blocked by safety filters. Try a different prompt.")

        image_bytes = response.images[0]._image_bytes
        
    except Exception as e:
        print(f"Error during Vertex AI image generation: {e}")
        raise Exception(f"Failed to generate product image: {e}")

    # 4. Upload the image bytes to Google Cloud Storage
    # Create a unique filename to avoid collisions
    filename = f"products/{uuid.uuid4()}.png"
    public_url = await _upload_to_gcs(image_bytes, filename)
    
    print(f"--- IMAGE GENERATED AND SAVED: {public_url} ---")
    return public_url


async def search_google_for_prompt(prompt: str) -> dict:
    """
    Performs a Google search using the Custom Search JSON API.
    """
    if not google_search_service:
        print("--- GOOGLE SEARCH CLIENT NOT INITIALIZED (SKIPPING SEARCH) ---")
        return {"error": "Google Search service is not configured."}
        
    print(f"--- GOOGLE SEARCH FOR PROMPT: '{prompt}' ---")
    try:
        result = (
            google_search_service.cse()
            .list(q=prompt, cx=settings.GOOGLE_CSE_ID, num=5)
            .execute()
        )
        print("--- GOOGLE SEARCH SUCCESSFUL ---")
        return result
    except HttpError as e:
        print(f"Error during Google Search API call: {e}")
        return {"error": f"Google Search failed: {e.reason}"}