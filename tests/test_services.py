import pytest
import sys
import os
from app.services import extract_skills, analyze_target_role
from app.models import Skill
from app.constants import JOB_ROLES
# from app.services import *
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Test Data ---
@pytest.fixture
def sample_text_swe():
    """Fixture for sample text biased towards a Software Engineer."""
    return """
    Skills:
    Python, Java, Git, Docker, Kubernetes, AWS, SQL, JavaScript, React
    """

@pytest.fixture
def sample_text_ds():
    """Fixture for sample text biased towards a Data Scientist."""
    return """
    Skills:
    Python, R, SQL, Pandas, Scikit-learn, TensorFlow, Matplotlib, Tableau
    """

def test_extract_skills_swe(sample_text_swe):
    """Tests if core SWE skills are extracted correctly."""
    skills = extract_skills(sample_text_swe)
    skill_names = {s.name.lower() for s in skills}
    
    assert "python" in skill_names
    assert "react" in skill_names
    assert "docker" in skill_names
    assert "git" in skill_names
    assert "sql" in skill_names
    assert "java" in skill_names
    assert "figma" not in skill_names

def test_extract_skills_ds(sample_text_ds):
    """Tests if core DS skills are extracted correctly."""
    skills = extract_skills(sample_text_ds)
    skill_names = {s.name.lower() for s in skills}
    
    assert "python" in skill_names
    assert "sql" in skill_names
    assert "pandas" in skill_names
    assert "tensorflow" in skill_names
    assert "scikit-learn" in skill_names
    assert "tableau" in skill_names
    assert "docker" not in skill_names

def test_target_role_analysis_swe(sample_text_swe):
    """Tests the skill gap analysis for a SWE role."""
    skills = extract_skills(sample_text_swe)
    target_role = "Software Engineer"
    analysis = analyze_target_role(skills, target_role)
    
    assert analysis is not None
    assert analysis['role'] == target_role
    assert "java" in analysis['required_found']
    assert "teamwork" in analysis['required_missing']
    assert "docker" in analysis['good_to_have_found']
    assert "agile" in analysis['good_to_have_missing']

def test_invalid_target_role(sample_text_swe):
    """Tests that a non-existent role returns None."""
    skills = extract_skills(sample_text_swe)
    target_role = "Galactic Emperor"
    analysis = analyze_target_role(skills, target_role)
    assert analysis is None