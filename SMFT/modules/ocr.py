import pytesseract
from PIL import Image
import os

# ===============================================================
# 🔴 THE FIX: POINT TO THE INSTALLED EXE ON YOUR COMPUTER
# ===============================================================
# If you installed it in the default location, this will work.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    """
    Uses Tesseract OCR to read text from an image file.
    """
    if not os.path.exists(image_path):
        return "Error: Image file not found."

    try:
        # Load image
        img = Image.open(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(img)
        
        return text.strip() if text else None

    except Exception as e:
        # If it fails, we return the error so you can see it in the report
        return f"Error during OCR: {str(e)}"