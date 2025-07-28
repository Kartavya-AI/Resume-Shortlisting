import os
import shutil
import tempfile
import logging
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from src.resume_shortlisting.crew import ResumeShortlistingCrew

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Shortlisting AI API",
    description="An API to shortlist resumes based on a job description using a CrewAI-powered team of agents.",
    version="1.0.0"
)

@app.get("/", tags=["Status"])
async def read_root():
    return {"status": "Resume Shortlisting API is running!"}

@app.post("/shortlist-resumes/", tags=["Resume Shortlisting"])
async def shortlist_resumes(
    job_description: str = Form(..., description="The full job description or user preferences for the desired candidate."),
    resumes: List[UploadFile] = File(..., description="One or more resume files (PDFs) to be analyzed.")
):
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Created temporary directory for request: {temp_dir}")

    try:
        for resume in resumes:
            file_path = os.path.join(temp_dir, resume.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)
            logger.info(f"Saved resume '{resume.filename}' to temporary directory.")

        inputs = {
            'job_description': job_description,
            'resume_folder': temp_dir
        }

        logger.info("Initializing and kicking off the Resume Shortlisting Crew...")
        crew_result = ResumeShortlistingCrew().run(inputs)
        
        logger.info("Crew has finished its work. Preparing the final response.")
        return JSONResponse(
            status_code=200,
            content={"final_report": crew_result}
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Successfully cleaned up temporary directory: {temp_dir}")
