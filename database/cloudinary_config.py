import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

cloudinary.config( 
  cloud_name = os.getenv("CLOUD_NAME"), 
  api_key = os.getenv("API_KEY"), 
  api_secret = os.getenv("API_SECRET"
) 
 
)

def upload_image(image_path):
    """Upload an image to Cloudinary and return the URL"""
    response = cloudinary.uploader.upload(image_path)
    return response["secure_url"]
