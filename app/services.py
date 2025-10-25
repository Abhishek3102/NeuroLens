import PyPDF2
import docx
import re
import spacy
import time
import logging
import asyncio
from io import BytesIO
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


from .models import AnalysisResponse, Skill, RoleMatch
from .constants import SKILL_CATEGORIES, JOB_ROLES
from .db_service import log_analysis_to_db
from .config import settings

# Get the logger for this module
logger = logging.getLogger(__name__)

# --- Text Extraction Functions ---

def extract_text_from_pdf(file_stream: BytesIO) -> str:
    """Extracts text from a PDF file stream."""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        logger.info("PDF text extracted successfully.")
    except Exception as e:
        logger.error(f"Error reading PDF: {e}", exc_info=True)
    return text

def extract_text_from_docx(file_stream: BytesIO) -> str:
    """Extracts text from a DOCX file stream."""
    text = ""
    try:
        doc = docx.Document(file_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
        logger.info("DOCX text extracted successfully.")
    except Exception as e:
        logger.error(f"Error reading DOCX: {e}", exc_info=True)
    return text

# --- Core Analysis Functions ---

def extract_skills(text: str) -> List[Skill]:
    """Extracts skills from text based on SKILL_CATEGORIES."""
    skills_found = []
    text_lower = text.lower()
    found_skill_names = set()

    for category, skills_list in SKILL_CATEGORIES.items():
        for skill in skills_list:
            skill_lower = skill.lower()
            if skill_lower in found_skill_names:
                continue
            
            pattern = r'\b' + re.escape(skill_lower) + r's?\b'
            
            if re.search(pattern, text_lower):
                skills_found.append(Skill(name=skill, category=category))
                found_skill_names.add(skill_lower)
                
    logger.info(f"Extracted {len(skills_found)} skills.")
    return skills_found

def analyze_experience(text: str, nlp_model) -> List[str]:
    """Analyzes text for experience using spaCy NER (Dates) and regex (years)."""
    experience_matches = []
    
    # 1. Use regex for "X years" patterns
    year_patterns = [
        r'\b(\d+)\s*(?:\+\s*)?years?\b', # "5 years", "5+ years"
        r'\b(\d+)-(\d+)\s*years?\b' # "5-7 years"
    ]
    for pattern in year_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            experience_matches.append(f"Mention of: {m.group()}")
            
    # 2. Use spaCy NER for DATE entities
    try:
        doc = nlp_model(text)
        date_entities = [ent.text.replace("\n", " ") for ent in doc.ents if ent.label_ == "DATE"]
        if date_entities:
            unique_dates = sorted(list(set(date_entities)), key=len, reverse=True)
            experience_matches.append("Key Dates Found:")
            experience_matches.extend(unique_dates[:10]) # Limit to 10
    except Exception as e:
        logger.warning(f"Spacy NER analysis failed: {e}", exc_info=True)

    logger.info(f"Found {len(experience_matches)} experience snippets.")
    return list(set(experience_matches))

def analyze_education(text: str) -> List[str]:
    """Analyzes text for education-related keywords."""
    education_keywords = [
        r'\b(?:B\.?S\.?|M\.?S\.?|Ph\.?D\.?|B\.?A\.?|M\.?B\.?A\.?|B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?)\b', # Degrees
        r'\bUniversity\b', r'\bCollege\b', r'\bInstitute of Technology\b',
        r'\bDegree\b', r'\bBachelor\b', r'\bMaster\b',
        r'\b(Cum Laude|Magna Cum Laude|Summa Cum Laude)\b' # Honors
    ]
    education_found = set()
    
    for pattern in education_keywords:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            context_start = max(0, m.start() - 30)
            context_end = min(len(text), m.end() + 30)
            context_snippet = text[context_start:context_end].replace("\n", " ").strip()
            education_found.add(context_snippet)
            
    logger.info(f"Found {len(education_found)} education snippets.")
    return list(education_found)

def suggest_role_matches(skills: List[Skill]) -> List[RoleMatch]:
    """Scores and suggests job roles based on found skills."""
    role_scores = {}
    skill_names_found = {s.name.lower() for s in skills}
    
    for role, requirements in JOB_ROLES.items():
        total_required = len(requirements["required_skills"])
        total_good_to_have = len(requirements["good_to_have"])
        
        required_found = skill_names_found.intersection(requirements["required_skills"])
        good_to_have_found = skill_names_found.intersection(requirements["good_to_have"])
        
        required_score = (len(required_found) / total_required) if total_required > 0 else 0
        good_to_have_score = (len(good_to_have_found) / total_good_to_have) if total_good_to_have > 0 else 0
        
        final_score = (required_score * 0.7 + good_to_have_score * 0.3) * 100
        role_scores[role] = final_score
        
    sorted_roles = sorted(role_scores.items(), key=lambda item: item[1], reverse=True)
    logger.info("Calculated role match scores.")
    return [RoleMatch(role=role, score=round(score, 2)) for role, score in sorted_roles]

def analyze_target_role(skills: List[Skill], target_role: str) -> Optional[Dict[str, Any]]:
    """Provides a detailed breakdown of skill match for a specific target role."""
    if target_role not in JOB_ROLES:
        logger.warning(f"Target role '{target_role}' not found in JOB_ROLES.")
        return None
        
    requirements = JOB_ROLES[target_role]
    skill_names_found = {s.name.lower() for s in skills}
    required_skills_set = set(requirements["required_skills"])
    good_to_have_set = set(requirements["good_to_have"])
    
    # Calculate score for target role (for logging)
    total_required = len(required_skills_set)
    total_good_to_have = len(good_to_have_set)
    required_found_count = len(skill_names_found.intersection(required_skills_set))
    good_to_have_found_count = len(skill_names_found.intersection(good_to_have_set))
    
    req_score = (required_found_count / total_required) if total_required > 0 else 0
    gth_score = (good_to_have_found_count / total_good_to_have) if total_good_to_have > 0 else 0
    final_score = (req_score * 0.7 + gth_score * 0.3) * 100
    
    logger.info(f"Target role analysis complete for '{target_role}'. Score: {final_score:.2f}")
    
    return {
        "role": target_role,
        "score": final_score,
        "required_found": sorted(list(skill_names_found.intersection(required_skills_set))),
        "required_missing": sorted(list(required_skills_set - skill_names_found)),
        "good_to_have_found": sorted(list(skill_names_found.intersection(good_to_have_set))),
        "good_to_have_missing": sorted(list(good_to_have_set - skill_names_found))
    }

# --- AI Feedback Generation (UPDATED) ---

async def get_personalized_feedback(analysis_data: Dict[str, Any]) -> str:
    """Calls the Gemini API to generate personalized feedback."""
    
    # --- Use the API key from settings ---
    apiKey = settings.GEMINI_API_KEY
    
    if not apiKey or apiKey == "YOUR_GEMINI_API_KEY_GOES_HERE":
        logger.error("GEMINI_API_KEY not configured in .env file.")
        return "Error: AI feedback service is not configured."

    try:
        genai.configure(api_key=apiKey)
    except Exception as e:
        logger.error(f"Error configuring GenerativeAI: {e}", exc_info=True)
        return "Error: Could not configure AI feedback service."

    prompt_template = f"""
    You are an expert, encouraging, and professional career coach. A user has uploaded their resume for analysis.
    Your task is to provide concise, actionable feedback in Markdown format (max 3-4 bullet points).

    **Analysis Data:**
    * **Target Role:** {analysis_data.get('role', 'N/A')}
    * **Skills Found:** {', '.join(analysis_data.get('required_found', [])) or 'None'}
    * **Critical Missing Skills:** {', '.join(analysis_data.get('required_missing', [])) or 'None'}
    * **'Good-to-Have' Missing Skills:** {', '.join(analysis_data.get('good_to_have_missing', [])) or 'None'}
    * **Total Skills Count:** {analysis_data.get('total_skills', 0)}

    **Instructions:**
    1.  Start with a positive reinforcement based on the skills they *do* have.
    2.  Identify the *most critical* 1-2 missing required skills. Suggest a specific, actionable way to learn them (e.g., "build a small project," "contribute to an open-source repo," "get a certification").
    3.  If no required skills are missing, suggest focusing on 1-2 "good-to-have" skills to stand out.
    4.  Provide one suggestion on how to tailor their resume *language* (e.g., "Use keywords like '{analysis_data.get('experience_keywords', ['...'])[0]}' to describe your experience...").
    5.  Keep the tone professional, supportive, and constructive. Do not be overly harsh.
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
    
    max_retries = 3
    delay = 1
    response = None # Define response outside try block to access in final except
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Generating AI feedback (attempt {attempt + 1})...")
            response = await model.generate_content_async(prompt_template)
            
            # --- FIX ---
            # Accessing response.text will raise an exception if
            # the finish_reason is not STOP (e.g., SAFETY, MAX_TOKENS).
            # This is more robust than checking enums or magic numbers.
            text_response = response.text
            # --- END FIX ---
            
            logger.info("AI feedback generated successfully.")
            return text_response
        
        except Exception as e:
            # This will catch the ValueError from response.text
            # as well as API call errors.
            logger.warning(f"Gemini API call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error("AI feedback failed after multiple retries.", exc_info=True)
                # Try to get the reason if possible, otherwise return generic error
                try:
                    # Check if response object exists and has candidates
                    if response and response.candidates:
                        reason_name = response.candidates[0].finish_reason.name
                        return f"Error: AI feedback generation failed (Reason: {reason_name})."
                    else:
                        return "Error: Unable to generate AI feedback (No response from model)."
                except Exception as inner_e:
                    logger.error(f"Error getting failure reason: {inner_e}")
                    return "Error: Unable to generate AI feedback at this time."
                
    return "Error: AI feedback generation failed."


# --- Main Service Orchestrator ---

async def analyze_resume_file(
    file_stream: BytesIO, 
    filename: str, 
    target_role: str,
    nlp_model,
    db_client: AsyncIOMotorClient # Added db_client parameter
) -> AnalysisResponse:
    """Orchestrates the full resume analysis pipeline."""
    
    start_time = time.time()
    
    # 1. Extract Text
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_stream)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_stream)
    else:
        raise ValueError("Unsupported file type")
        
    if not text.strip():
        logger.warning(f"Could not extract text from file: {filename}. It may be empty or image-based.")
        raise ValueError("Could not extract text from the document. It might be empty or image-based.")

    # 2. Run Analyses (CPU-bound tasks)
    # These are sync functions, they will run in the main thread.
    skills = extract_skills(text)
    experience_summary = analyze_experience(text, nlp_model)
    education_summary = analyze_education(text)
    role_matches = suggest_role_matches(skills)
    target_role_analysis = analyze_target_role(skills, target_role)
    
    # 3. Prepare Data and Get AI Feedback (I/O-bound task)
    feedback_data = {}
    target_score = 0.0
    if target_role_analysis:
        feedback_data = target_role_analysis.copy()
        feedback_data["total_skills"] = len(skills)
        feedback_data["experience_keywords"] = JOB_ROLES.get(target_role, {}).get("experience_keywords", [])
        target_score = target_role_analysis.get('score', 0.0)

    # Run AI feedback generation asynchronously
    personalized_feedback = await get_personalized_feedback(feedback_data)

    # 4. Log to Database (I/O-bound task)
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    
    log_document = {
        "timestamp": datetime.utcnow(),
        "file_name": filename,
        "target_role": target_role,
        "match_score": target_score,
        "skills_found_count": len(skills),
        "analysis_duration_ms": duration_ms
    }
    
    # Log to DB asynchronously
    await log_analysis_to_db(db_client, log_document)

    # 5. Construct Final Response
    return AnalysisResponse(
        fileName=filename,
        extractedText=text[:2000] + "...", # Truncate text
        skillsFound=skills,
        roleMatches=role_matches,
        targetRoleAnalysis=target_role_analysis,
        experienceSummary=experience_summary,
        educationSummary=education_summary,
        personalizedFeedback=personalized_feedback
    )

