import os
from fastapi import UploadFile, HTTPException
from app.core.fdpbd_analysis import run_fdpbd_analysis
from app.utils.file_upload import save_uploaded_file


async def analyze_fdpbd(params: dict, file: UploadFile) -> dict:
    """Run FD-PBD analysis with given parameters and uploaded file."""
    # Save uploaded file
    try:
        filename = await save_uploaded_file(file)
        file_path = f"data/{filename}.txt"

        # Run analysis
        result = run_fdpbd_analysis(params, filename)

        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)

        return result
    except Exception as e:
        # Ensure file is cleaned up on error
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
