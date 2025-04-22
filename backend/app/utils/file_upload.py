import os
import uuid
from fastapi import UploadFile, HTTPException


async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file to data/ directory and return filename without extension."""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")

    # Ensure data/ directory exists
    os.makedirs("data", exist_ok=True)

    # Generate unique filename
    filename = f"{uuid.uuid4()}"
    file_path = f"data/{filename}.txt"

    # Save file
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        return filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
