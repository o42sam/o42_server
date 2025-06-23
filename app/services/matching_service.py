# app/services/matching_service.py

import torch
import httpx
from PIL import Image
from io import BytesIO
from motor.motor_asyncio import AsyncIOMotorDatabase
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.crud import purchase_order, sale_order

# --- Load Models at Startup ---
# This ensures that the models are loaded into memory only once, not on every call.
# This is crucial for performance.

# 1. Load the Sentence Transformer model for text similarity.
# 'all-MiniLM-L6-v2' is a small but powerful model for semantic search.
try:
    print("Loading Text Similarity Model (SentenceTransformer)...")
    text_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Text Similarity Model loaded successfully.")
except Exception as e:
    print(f"CRITICAL: Could not load SentenceTransformer model. Text matching will fail. Error: {e}")
    text_model = None

# 2. Load the CLIP model for image similarity.
# 'openai/clip-vit-base-patch32' is the standard CLIP model.
try:
    print("Loading Image Similarity Model (CLIP)...")
    image_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    image_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    print("Image Similarity Model loaded successfully.")
except Exception as e:
    print(f"CRITICAL: Could not load CLIP model. Image matching will fail. Error: {e}")
    image_model = None
    image_processor = None


# --- AI/ML Model Service Implementations ---

async def get_image_similarity(image1_url: str, image2_url: str) -> float:
    """
    Calculates the similarity between two images using the CLIP model.
    It downloads images from URLs, generates embeddings, and computes their cosine similarity.
    """
    if not image_model or not image_processor:
        print("WARNING: Image model not loaded. Skipping image similarity calculation.")
        return 0.0

    try:
        # Asynchronously download image data
        async with httpx.AsyncClient() as client:
            response1 = await client.get(image1_url, timeout=30)
            response1.raise_for_status()
            image1 = Image.open(BytesIO(response1.content))

            response2 = await client.get(image2_url, timeout=30)
            response2.raise_for_status()
            image2 = Image.open(BytesIO(response2.content))

        # Process images and get embeddings
        with torch.no_grad(): # Disable gradient calculation for efficiency
            inputs = image_processor(images=[image1, image2], return_tensors="pt", padding=True)
            image_features = image_model.get_image_features(**inputs)
        
        # Normalize features
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(image_features[0].unsqueeze(0), image_features[1].unsqueeze(0))
        
        score = float(similarity[0][0])
        print(f"SUCCESS: Image similarity score between {image1_url} and {image2_url} is {score:.4f}")
        return score

    except Exception as e:
        print(f"ERROR: Could not calculate image similarity. Reason: {e}")
        return 0.0


async def get_text_similarity(text1: str, text2: str) -> float:
    """
    Calculates the similarity between two text strings using a Sentence Transformer model.
    """
    if not text_model:
        print("WARNING: Text model not loaded. Skipping text similarity calculation.")
        return 0.0
        
    try:
        # Generate embeddings for both texts
        embeddings = text_model.encode([text1, text2])
        
        # Calculate cosine similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])
        
        score = float(similarity[0][0])
        print(f"SUCCESS: Text similarity score is {score:.4f}")
        return score
    except Exception as e:
        print(f"ERROR: Could not calculate text similarity. Reason: {e}")
        return 0.0


# --- Main Matching Logic (No changes needed here) ---

async def run_matching_cycle(db: AsyncIOMotorDatabase, new_order_id: str, order_type: str):
    """
    The main background task for finding and storing order matches.
    This function now calls the actual AI/ML implementations.
    """
    print(f"Starting matching cycle for new {order_type} order: {new_order_id}")

    if order_type == "purchase":
        # ... (logic remains exactly the same as before) ...
        new_po = await purchase_order.purchase_order.get(db, id=new_order_id)
        if not new_po: return
        all_so = await sale_order.sale_order.get_multi(db, limit=1000)
        scored_matches = []
        for so in all_so:
            so_product = await db.products.find_one({"_id": so["product_id"]})
            if not so_product: continue
            score = 0
            if so_product.get("images") and new_po.get("product_image"):
                score = await get_image_similarity(so_product["images"][0], new_po["product_image"])
            elif so_product.get("description") and new_po.get("product_description"):
                score = await get_text_similarity(so_product["description"], new_po["product_description"])
            if score > 0:
                scored_matches.append({"order_id": str(so["_id"]), "score": score})
        top_5_so_matches = sorted(scored_matches, key=lambda x: x["score"], reverse=True)[:5]
        await purchase_order.purchase_order.update(db, db_obj=new_po, obj_in={"matching_sale_orders": top_5_so_matches})
        print(f"Updated Purchase Order {new_order_id} with {len(top_5_so_matches)} matches.")
        
    elif order_type == "sale":
        # ... (logic remains exactly the same as before) ...
        new_so = await sale_order.sale_order.get(db, id=new_order_id)
        if not new_so: return
        so_product = await db.products.find_one({"_id": new_so["product_id"]})
        if not so_product: return
        all_po = await purchase_order.purchase_order.get_multi(db, limit=1000)
        scored_matches = []
        for po in all_po:
            score = 0
            if so_product.get("images") and po.get("product_image"):
                score = await get_image_similarity(so_product["images"][0], po["product_image"])
            elif so_product.get("description") and po.get("product_description"):
                score = await get_text_similarity(so_product["description"], po["product_description"])
            if score > 0:
                scored_matches.append({"order_id": str(po["_id"]), "score": score})
        top_5_po_matches = sorted(scored_matches, key=lambda x: x["score"], reverse=True)[:5]
        await sale_order.sale_order.update(db, db_obj=new_so, obj_in={"matching_purchase_orders": top_5_po_matches})
        print(f"Updated Sale Order {new_order_id} with {len(top_5_po_matches)} matches.")

    print(f"Matching cycle finished for order: {new_order_id}")