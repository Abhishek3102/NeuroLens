from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Skill(BaseModel):
    """A single skill identified in the resume."""
    name: str = Field(..., description="The name of the skill.", example="Python")
    category: str = Field(..., description="The category the skill belongs to.", example="Programming Languages")

class RoleMatch(BaseModel):
    """A job role and the calculated match score."""
    role: str = Field(..., description="The name of the job role.", example="Software Engineer")
    score: float = Field(..., description="The match score (0-100) for this role.", example=85.5)

class AnalysisResponse(BaseModel):
    """The complete analysis response returned by the API."""
    
    fileName: str = Field(..., description="The name of the uploaded file.", example="my_resume.pdf")
    
    extractedText: str = Field(..., description="A truncated snippet of the text.", example="John Doe...")
    
    skillsFound: List[Skill] = Field(..., description="A list of all skills identified.")
    
    roleMatches: List[RoleMatch] = Field(..., description="A sorted list of all potential job roles and their match scores.")
    
    targetRoleAnalysis: Optional[Dict[str, Any]] = Field(
        None, 
        description="A detailed breakdown of skill matches for the user-specified target role.",
        example={
            "role": "Software Engineer",
            "required_found": ["python", "git"],
            "required_missing": ["java", "sql"],
            # ... etc
        }
    )
    
    experienceSummary: List[str] = Field(..., description="A list of strings summarizing found experience.")
    
    educationSummary: List[str] = Field(..., description="A list of snippets related to education.")
    
    personalizedFeedback: str = Field(..., description="Actionable, AI-generated feedback in Markdown.")