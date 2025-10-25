import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import spacy

from .models import AnalysisResponse
from .services import analyze_resume_file
from .db_service import connect_to_mongo, close_mongo_connection, get_analysis_metrics
from .logging_config import setup_logging

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Load the spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    logger.error("Spacy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

app = FastAPI(
    title="AI Resume Analyzer API",
    description="Analyzes resumes, matches roles, and provides AI feedback.",
    version="1.0.0"
)

# --- CORS Middleware ---
# Essential for your Next.js frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your Next.js app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Connection Events ---
@app.on_event("startup")
async def startup_event():
    """Connects to MongoDB on app startup."""
    logger.info("Starting up FastAPI application...")
    if nlp is None:
        logger.warning("spaCy model not loaded. Analysis will be limited.")
    app.state.db_client = await connect_to_mongo()
    if app.state.db_client:
        logger.info("MongoDB connection established.")
    else:
        logger.error("Failed to establish MongoDB connection on startup.")

@app.on_event("shutdown")
async def shutdown_event():
    """Closes MongoDB connection on app shutdown."""
    logger.info("Shutting down FastAPI application...")
    await close_mongo_connection(app.state.db_client)
    logger.info("MongoDB connection closed.")

# --- API Endpoints ---
@app.get("/")
async def root():
    """Root endpoint to check API health."""
    return {"message": "AI Resume Analyzer API is running."}

@app.post("/analyze/", response_model=AnalysisResponse)
async def analyze_resume(
    request: Request,
    resume_file: UploadFile = File(..., description="The resume file (PDF or DOCX)"),
    target_role: str = Form(..., description="The target job role (e.g., 'Software Engineer')")
):
    """
    Analyzes a resume file against a target job role.
    """
    if nlp is None:
        logger.error("spaCy model not loaded, cannot process request.")
        raise HTTPException(status_code=500, detail="NLP model is not loaded on the server.")
    
    # Get the database client from the app state
    db_client = request.app.state.db_client
    if db_client is None:
        logger.error("Database connection not available.")
        raise HTTPException(status_code=500, detail="Database connection is not available.")

    try:
        file_contents = await resume_file.read()
        file_stream = BytesIO(file_contents)
    except Exception as e:
        logger.error(f"Error reading file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    if not (resume_file.filename.endswith(".pdf") or resume_file.filename.endswith(".docx")):
        logger.warning(f"Invalid file type uploaded: {resume_file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .pdf or .docx file.")

    logger.info(f"Analyzing resume: {resume_file.filename} for role: {target_role}")

    try:
        analysis_result = await analyze_resume_file(
            file_stream=file_stream,
            filename=resume_file.filename,
            target_role=target_role,
            nlp_model=nlp,
            db_client=db_client  # Pass the DB client to the service
        )
        return analysis_result
    
    except ValueError as ve:
        logger.warning(f"Value error during analysis: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/metrics/")
async def get_metrics(request: Request):
    """
    Retrieves performance and usage metrics from the database.
    """
    db_client = request.app.state.db_client
    if db_client is None:
        logger.error("Database connection not available for /metrics.")
        raise HTTPException(status_code=500, detail="Database connection is not available.")
        
    logger.info("Fetching /metrics")
    try:
        metrics = await get_analysis_metrics(db_client)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve metrics.")


# Run using: uvicorn app.main:app --reload