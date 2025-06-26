import cv2
import numpy as np
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
from sklearn.metrics.pairwise import cosine_similarity
import json
# Import the text model we already loaded in the matching service
from app.services.matching_service import text_model
from app.models.product import ProductCategory

# --- Video Processing ---

def extract_frame_from_video(video_bytes: bytes) -> bytes:
    """
    Extracts a single frame from the middle of a video byte stream.
    Returns the frame as JPEG image bytes.
    """
    # Write video bytes to a temporary file, as OpenCV works best with file paths
    temp_video_path = "/tmp/temp_video.mp4"
    with open(temp_video_path, "wb") as f:
        f.write(video_bytes)

    cap = cv2.VideoCapture(temp_video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file.")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Go to the frame in the middle of the video
        middle_frame_index = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_index)

        ret, frame = cap.read()
        if not ret:
            raise ValueError("Could not read the middle frame of the video.")

        # Encode the frame as a JPEG image in memory
        is_success, buffer = cv2.imencode(".jpg", frame)
        if not is_success:
            raise ValueError("Could not encode frame to JPEG.")

        return buffer.tobytes()
    finally:
        cap.release()


# --- AI Model Services ---

async def generate_product_details_from_media(media_bytes: bytes, mime_type: str) -> dict:
    """
    Uses the Gemini Pro Vision model to generate a name, description, and keywords
    from a given image or video frame.
    """
    if not mime_type.startswith("image/"):
        raise ValueError("Invalid MIME type for media analysis, must be an image.")

    model = GenerativeModel("gemini-1.5-flash-001")

    prompt = """
    You are an expert e-commerce catalog manager for a Nigerian marketplace called 'o42'.
    Analyze this image of a product. Based ONLY on the visual information, provide a response in valid JSON format with three keys: "name", "description", and "keywords".

    - "name": A concise, marketable product title suitable for an online store. Be specific.
    - "description": A detailed, appealing paragraph describing the product's likely features, material, color, and condition as seen in the image.
    - "keywords": A list of 5-7 relevant string keywords for the product that will help in categorization.
    
    Example response format:
    {
      "name": "Blue Patterned Short-Sleeve Shirt",
      "description": "A stylish short-sleeve button-up shirt featuring a vibrant blue and white pattern. Made from a lightweight fabric, likely cotton, perfect for warm weather. The shirt appears to be in excellent, brand-new condition.",
      "keywords": ["men's fashion", "shirt", "casual wear", "patterned shirt", "blue", "short sleeve"]
    }
    """

    media_part = Part.from_data(data=media_bytes, mime_type=mime_type)
    
    generation_config = {"max_output_tokens": 2048, "temperature": 0.4, "top_p": 1.0, "top_k": 32}
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    try:
        response = await model.generate_content_async(
            [media_part, prompt],
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        # Assuming the model returns a clean JSON string
        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise ValueError("Failed to generate product details from media.")


def find_best_category(text_to_compare: str) -> str:
    """
    Finds the most semantically similar category from the ProductCategory enum
    using the pre-loaded sentence-transformer model.
    """
    if not text_model:
        raise RuntimeError("Text similarity model is not loaded.")

    # Get all possible category values from the enum
    categories = [item.value for item in ProductCategory]
    
    # Generate embeddings
    text_embedding = text_model.encode([text_to_compare])
    category_embeddings = text_model.encode(categories)
    
    # Calculate similarity scores
    similarities = cosine_similarity(text_embedding, category_embeddings)
    
    # Find the index of the highest score
    best_match_index = np.argmax(similarities)
    
    return categories[best_match_index]