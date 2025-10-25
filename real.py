from flask import Flask, request, jsonify
import PyPDF2
import docx
import re
import spacy
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

app = Flask(__name__)

SKILL_CATEGORIES = {
    "Programming Languages": ["python", "java", "javascript", "c++", "ruby", "php", "swift", "kotlin", "r", "matlab"],
    "Web Development": ["html", "css", "react", "angular", "vue", "node.js", "django", "flask", "asp.net"],
    "Database": ["sql", "mysql", "postgresql", "mongodb", "oracle", "redis", "elasticsearch"],
    "Cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"],
    "Machine Learning": ["tensorflow", "pytorch", "scikit-learn", "keras", "opencv", "nlp", "computer vision"],
    "Tools": ["git", "jenkins", "jira", "confluence", "slack", "postman", "swagger"],
    "Soft Skills": ["leadership", "communication", "teamwork", "problem solving", "analytical", "project management"]
}

JOB_ROLES = {
    "Software Engineer": {
        "required_skills": ["python", "java", "javascript", "sql", "git", "algorithms", "data structures"],
        "good_to_have": ["docker", "kubernetes", "aws", "ci/cd", "agile"],
        "experience_keywords": ["development", "implementation", "testing", "debugging", "optimization"]
    },
    "Data Scientist": {
        "required_skills": ["python", "r", "sql", "machine learning", "statistics", "data analysis"],
        "good_to_have": ["tensorflow", "pytorch", "big data", "spark", "tableau"],
        "experience_keywords": ["analysis", "modeling", "visualization", "research", "prediction"]
    },
    "Web Developer": {
        "required_skills": ["html", "css", "javascript", "react", "node.js", "responsive design"],
        "good_to_have": ["typescript", "vue", "angular", "webpack", "sass"],
        "experience_keywords": ["frontend", "backend", "full-stack", "web applications", "apis"]
    },
    "DevOps Engineer": {
        "required_skills": ["linux", "aws", "docker", "kubernetes", "jenkins", "terraform"],
        "good_to_have": ["python", "ansible", "prometheus", "elk stack", "nginx"],
        "experience_keywords": ["automation", "deployment", "monitoring", "infrastructure", "security"]
    }
}

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_skills(text):
    skills = {}
    text_lower = text.lower()
    
    for category, skill_list in SKILL_CATEGORIES.items():
        found_skills = []
        for skill in skill_list:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.append(skill)
        if found_skills:
            skills[category] = found_skills
    
    return skills

def analyze_experience(text):
    experience_patterns = [
        r'\b(\d+)\s*(?:\+\s*)?years?\b',
        r'\b(\d{4})\s*-\s*(?:present|current|now|\d{4})\b',
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b'
    ]
    
    experience_matches = []
    for pattern in experience_patterns:
        matches = re.finditer(pattern, text.lower())
        experience_matches.extend([m.group() for m in matches])
    
    return experience_matches

def suggest_role_match(skills_found):
    role_scores = {}
    for role, requirements in JOB_ROLES.items():
        required_match = len(set(requirements["required_skills"]).intersection(
            [skill for skills in skills_found.values() for skill in skills]
        )) / len(requirements["required_skills"])
        
        good_to_have_match = len(set(requirements["good_to_have"]).intersection(
            [skill for skills in skills_found.values() for skill in skills]
        )) / len(requirements["good_to_have"])
        
        role_scores[role] = (required_match * 0.7 + good_to_have_match * 0.3) * 100
    
    return role_scores

def analyze_education(text):
    education_patterns = [
        r'\b(?:bachelor|master|phd|b\.?tech|m\.?tech|b\.?e|m\.?e|b\.?sc|m\.?sc)\b',
        r'\buniversity\b',
        r'\bcollege\b',
        r'\bdegree\b'
    ]
    
    education = []
    for pattern in education_patterns:
        matches = re.finditer(pattern, text.lower())
        education.extend([m.group() for m in matches])
    
    return list(set(education))

@app.route("/analyze_resume", methods=["POST"])
def analyze_resume():
    try:
        resume_file = request.files['resume']
        role_selection = request.form.get("role_selection")
        
        if resume_file:
            file_extension = resume_file.filename.split(".")[-1].lower()
            if file_extension == "pdf":
                resume_text = extract_text_from_pdf(resume_file)
            else:
                resume_text = extract_text_from_docx(resume_file)
            
            extracted_skills = extract_skills(resume_text)
            experience_found = analyze_experience(resume_text)
            education_found = analyze_education(resume_text)
            role_matches = suggest_role_match(extracted_skills)
            
            match_score = role_matches.get(role_selection, 0)
            total_skills = sum(len(skills) for skills in extracted_skills.values())
            
            missing_required = set(JOB_ROLES[role_selection]["required_skills"]) - \
                              set([skill for skills in extracted_skills.values() for skill in skills])
            
            missing_good_to_have = set(JOB_ROLES[role_selection]["good_to_have"]) - \
                                  set([skill for skills in extracted_skills.values() for skill in skills])
            
            result = {
                "role_match_score": match_score,
                "skills_found": extracted_skills,
                "experience_found": experience_found,
                "education_found": education_found,
                "missing_required_skills": list(missing_required),
                "missing_good_to_have": list(missing_good_to_have),
                "total_skills": total_skills
            }
            
            return jsonify(result), 200
        else:
            return jsonify({"error": "Resume file is required"}), 400
        
    except Exception as e:
        return jsonify({"error": f"Error analyzing resume: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
