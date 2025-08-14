import os
import tempfile
import shutil
from typing import List, Optional
from pathlib import Path
import logging
import traceback

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
import aiofiles

from src.resume_shortlisting.crew import ResumeShortlistingCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Shortlisting API",
    description="AI-powered resume screening and candidate evaluation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class JobAnalysisResponse(BaseModel):
    must_have_skills: List[str] = Field(..., description="List of must-have skills")
    nice_to_have_skills: List[str] = Field(..., description="List of nice-to-have skills")
    required_experience: str = Field(..., description="Required years of experience")
    preferred_industries: List[str] = Field(..., description="Preferred industries")

class CandidateEvaluation(BaseModel):
    name: str = Field(..., description="Candidate's full name")
    mobile: str = Field(..., description="Candidate's mobile number")
    score: float = Field(..., ge=1, le=10, description="Score from 1 to 10")
    questions: List[str] = Field(..., description="Interview questions for the candidate")
    reasoning: str = Field(..., description="Reasoning for the score")

class ShortlistResponse(BaseModel):
    job_analysis: str = Field(..., description="Job description analysis")
    candidates: List[CandidateEvaluation] = Field(..., description="List of evaluated candidates")
    total_candidates: int = Field(..., description="Total number of candidates processed")

class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

# Global variables
crew_instance = None
temp_dir = None

# Dependency to get API key from environment
def get_api_key():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY environment variable not set"
        )
    return api_key

# Startup event
@app.on_event("startup")
async def startup_event():
    global crew_instance, temp_dir
    try:
        logger.info("Starting Resume Shortlisting API...")
        
        # Create temp directory for file uploads
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Initialize CrewAI with API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        
        crew_instance = ResumeShortlistingCrew(api_key=api_key)
        logger.info("CrewAI instance initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    global temp_dir
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")

# Cleanup background task
async def cleanup_files(file_paths: List[str]):
    """Background task to clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {str(e)}")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Resume Shortlisting API is running",
        version="1.0.0"
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Resume Shortlisting API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Main shortlisting endpoint
@app.post(
    "/shortlist-resumes",
    response_model=ShortlistResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def shortlist_resumes(
    background_tasks: BackgroundTasks,
    job_description: str = Form(..., description="Job description text"),
    resume_files: List[UploadFile] = File(..., description="List of resume PDF files"),
    api_key: str = Depends(get_api_key)
):
    """
    Main endpoint to shortlist resumes based on job description.
    
    - **job_description**: The job description text
    - **resume_files**: List of PDF resume files to evaluate
    
    Returns evaluated candidates with scores, interview questions, and reasoning.
    """
    global crew_instance, temp_dir
    
    if not crew_instance:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CrewAI instance not initialized"
        )
    
    saved_files = []
    
    try:
        # Validate inputs
        if not job_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description cannot be empty"
            )
        
        if not resume_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one resume file is required"
            )
        
        if len(resume_files) > 20:  # Limit number of resumes
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 resume files allowed"
            )
        
        logger.info(f"Processing {len(resume_files)} resume files")
        
        # Save uploaded files to temporary directory
        for file in resume_files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is not a PDF"
                )
            
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds 5MB size limit"
                )
            
            file_path = os.path.join(temp_dir, file.filename)
            saved_files.append(file_path)
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"Saved file: {file.filename}")
        
        # Prepare resume paths for CrewAI
        resume_paths_str = "\n".join([f"Resume file: {path}" for path in saved_files])
        
        # Execute CrewAI workflow
        logger.info("Starting CrewAI workflow...")
        
        inputs = {
            'job_description': job_description,
            'resumes': resume_paths_str
        }
        
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        logger.info("CrewAI workflow completed")
        
        # Schedule cleanup of temporary files
        background_tasks.add_task(cleanup_files, saved_files)
        
        # Parse the result and format response
        response_data = parse_crew_result(result, len(resume_files))
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        if saved_files:
            background_tasks.add_task(cleanup_files, saved_files)
        raise
        
    except Exception as e:
        logger.error(f"Error processing resumes: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Schedule cleanup
        if saved_files:
            background_tasks.add_task(cleanup_files, saved_files)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resumes: {str(e)}"
        )

def parse_crew_result(result, total_candidates: int) -> ShortlistResponse:
    """
    Parse the CrewAI result and format it into a structured response
    """
    try:
        result_text = str(result)
        logger.info(f"Raw result text: {result_text}")
        
        candidates = []
        job_analysis = ""
        
        # Look for table patterns in the result
        if "| Name |" in result_text and "| Mobile |" in result_text and "| Score |" in result_text:
            # Split by lines and find the table
            lines = result_text.split('\n')
            table_started = False
            header_found = False
            
            for line in lines:
                line = line.strip()
                
                # Check if this is the header line
                if "| Name |" in line and "| Mobile |" in line and "| Score |" in line:
                    header_found = True
                    continue
                
                # Skip separator line (usually contains dashes)
                if header_found and line.startswith('|') and '-' in line:
                    table_started = True
                    continue
                
                # Parse data rows
                if table_started and line.startswith('|') and line.endswith('|'):
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first and last
                    
                    if len(cells) >= 5:
                        try:
                            name = cells[0].strip()
                            mobile = cells[1].strip()
                            score_str = cells[2].strip()
                            questions_str = cells[3].strip()
                            reasoning = cells[4].strip()
                            
                            # Clean up HTML tags and special characters
                            questions_str = questions_str.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                            reasoning = reasoning.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                            
                            # Parse score - look for number/10 pattern or standalone number
                            import re
                            score_match = re.search(r'(\d+(?:\.\d+)?)', score_str)
                            if score_match:
                                score = float(score_match.group(1))
                                # If score appears to be in format "9/10", keep as is
                                # Otherwise ensure it's between 1-10
                                if score > 10:
                                    score = score / 10.0  # Convert percentage to 10-point scale
                                score = max(1.0, min(10.0, score))
                            else:
                                score = 5.0  # Default score
                            
                            # Parse questions - split by numbered points or line breaks
                            questions_list = []
                            if questions_str:
                                # Split by numbered patterns (1. 2. 3.) or line breaks
                                question_parts = re.split(r'(?:\d+\.\s*|\n)', questions_str)
                                for part in question_parts:
                                    part = part.strip()
                                    if part and len(part) > 5:  # Filter out very short fragments
                                        # Ensure question ends with question mark
                                        if not part.endswith('?'):
                                            part += '?'
                                        questions_list.append(part)
                            
                            if not questions_list:
                                questions_list = ["Tell me about your experience relevant to this role?"]
                            
                            # Clean up name and mobile
                            if not name or name.lower() in ['not found', 'n/a', '']:
                                name = f"Candidate {len(candidates) + 1}"
                            
                            if not mobile or mobile.lower() in ['not found', 'n/a', '']:
                                mobile = "Not available"
                            
                            candidate = CandidateEvaluation(
                                name=name,
                                mobile=mobile,
                                score=score,
                                questions=questions_list,
                                reasoning=reasoning
                            )
                            candidates.append(candidate)
                            
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Failed to parse candidate row: {line}. Error: {e}")
                            continue
                
                # If we haven't started the table yet, this might be job analysis
                elif not header_found:
                    if line and not line.startswith('```'):
                        job_analysis += line + "\n"
        
        # Clean up job analysis
        job_analysis = job_analysis.strip()
        if not job_analysis:
            job_analysis = "Job requirements analysis completed."
        
        # If no candidates were parsed but we have table-like content, try alternate parsing
        if not candidates and ("|" in result_text):
            logger.warning("Attempting alternative parsing method...")
            # Try a more flexible parsing approach
            table_lines = [line for line in result_text.split('\n') if '|' in line and len(line.split('|')) >= 6]
            
            for line in table_lines:
                if 'Name' in line and 'Mobile' in line:  # Skip header
                    continue
                if '---' in line or '===' in line:  # Skip separator
                    continue
                
                parts = line.split('|')
                if len(parts) >= 6:
                    try:
                        name = parts[1].strip() if len(parts) > 1 else f"Candidate {len(candidates) + 1}"
                        mobile = parts[2].strip() if len(parts) > 2 else "Not available"
                        score_str = parts[3].strip() if len(parts) > 3 else "5"
                        questions_str = parts[4].strip() if len(parts) > 4 else ""
                        reasoning = parts[5].strip() if len(parts) > 5 else "Analysis completed"
                        
                        # Parse score
                        import re
                        score_match = re.search(r'(\d+(?:\.\d+)?)', score_str)
                        score = float(score_match.group(1)) if score_match else 5.0
                        score = max(1.0, min(10.0, score))
                        
                        # Parse questions
                        questions_list = [q.strip() + ('?' if not q.strip().endswith('?') else '') 
                                        for q in questions_str.split('\n') if q.strip()]
                        if not questions_list:
                            questions_list = ["Tell me about your experience relevant to this role?"]
                        
                        candidate = CandidateEvaluation(
                            name=name if name else f"Candidate {len(candidates) + 1}",
                            mobile=mobile if mobile else "Not available",
                            score=score,
                            questions=questions_list,
                            reasoning=reasoning if reasoning else "Analysis completed"
                        )
                        candidates.append(candidate)
                        
                    except Exception as e:
                        logger.warning(f"Alternative parsing failed for line: {line}. Error: {e}")
                        continue
        
        # If still no candidates, create a fallback
        if not candidates:
            logger.warning("No candidates parsed from result, creating fallback response")
            candidates.append(CandidateEvaluation(
                name=f"Candidate 1",
                mobile="Contact information not extracted",
                score=5.0,
                questions=["Tell me about your experience relevant to this role?", "What interests you about this position?"],
                reasoning="Resume processed but detailed extraction needs manual review"
            ))
        
        return ShortlistResponse(
            job_analysis=job_analysis,
            candidates=candidates,
            total_candidates=total_candidates
        )
        
    except Exception as e:
        logger.error(f"Error parsing crew result: {str(e)}")
        logger.error(f"Result content: {str(result)}")
        
        # Return a fallback response
        return ShortlistResponse(
            job_analysis="Job analysis completed - manual review recommended",
            candidates=[CandidateEvaluation(
                name="Candidate 1",
                mobile="Not available", 
                score=5.0,
                questions=["Tell me about your experience relevant to this role?"],
                reasoning="Error occurred during processing - manual review needed"
            )],
            total_candidates=total_candidates
        )

# Additional utility endpoints

@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "name": "Resume Shortlisting API",
        "version": "1.0.0",
        "endpoints": {
            "POST /shortlist-resumes": "Main endpoint to shortlist resumes",
            "GET /health": "Health check endpoint",
            "GET /api/info": "API information",
            "GET /docs": "Interactive API documentation",
            "GET /redoc": "Alternative API documentation"
        },
        "max_file_size": "5MB",
        "max_files": 20,
        "supported_formats": ["PDF"]
    }

# Error handler
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            status_code=422
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error", 
            detail="An unexpected error occurred",
            status_code=500
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)