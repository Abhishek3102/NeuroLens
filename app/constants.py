SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "ruby", 
        "php", "swift", "kotlin", "r", "matlab", "sql", "scala", "perl", "rust"
    ],
    "Web Development (Frontend)": [
        "html", "css", "react", "angular", "vue", "vue.js", "next.js", "nextjs",
        "svelte", "jquery", "bootstrap", "tailwind", "tailwindcss", "sass", "less", "webpack", "babel"
    ],
    "Web Development (Backend)": [
        "node.js", "nodejs", "express", "django", "flask", "fastapi", "ruby on rails", 
        "spring", "spring boot", ".net", "asp.net", "laravel"
    ],
    "Database Systems": [
        "mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite", 
        "microsoft sql server", "sql server", "cassandra", "elasticsearch", "dynamodb", "firebase"
    ],
    "DevOps & Cloud": [
        "aws", "azure", "gcp", "google cloud platform", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "gitlab ci", "github actions", "ci/cd", 
        "prometheus", "grafana", "linux", "bash", "powershell", "nginx", "apache"
    ],
    "Data Science & ML": [
        "tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy", "scipy", 
        "matplotlib", "seaborn", "jupyter", "spark", "apache spark", "hadoop", "nlp", 
        "computer vision", "opencv", "d3.js", "tableau", "power bi", "looker"
    ],
    "Project Management & Tools": [
        "agile", "scrum", "kanban", "jira", "confluence", "trello", "asana", "git", 
        "github", "gitlab", "bitbucket", "svn", "project management"
    ],
    "Soft Skills": [
        "leadership", "communication", "teamwork", "problem solving", "analytical", 
        "critical thinking", "collaboration", "mentoring", "adaptability", "time management"
    ]
}

JOB_ROLES = {
    "Software Engineer": {
        "required_skills": ["python", "java", "javascript", "sql", "git", "teamwork"],
        "good_to_have": ["docker", "kubernetes", "aws", "ci/cd", "agile", "react", "node.js", "c++"],
        "experience_keywords": ["development", "implementation", "testing", "debugging", "optimization", "code review"]
    },
    "Data Scientist": {
        "required_skills": ["python", "r", "sql", "pandas", "scikit-learn", "matplotlib"],
        "good_to_have": ["tensorflow", "pytorch", "spark", "tableau", "power bi", "nlp", "computer vision", "aws"],
        "experience_keywords": ["analysis", "modeling", "visualization", "research", "prediction", "a/b testing", "algorithms"]
    },
    "Frontend Developer": {
        "required_skills": ["html", "css", "javascript", "react", "git", "api"],
        "good_to_have": ["typescript", "vue", "angular", "next.js", "tailwind", "figma", "sass", "webpack"],
        "experience_keywords": ["frontend", "ui", "user interface", "web applications", "responsive", "cross-browser"]
    },
    "Backend Developer": {
        "required_skills": ["node.js", "python", "java", "sql", "api", "rest", "git", "mongodb", "postgresql"],
        "good_to_have": ["docker", "kubernetes", "aws", "gcp", "django", "flask", "spring boot", "microservices", "graphql"],
        "experience_keywords": ["backend", "api development", "database design", "server-side", "microservices", "performance"]
    },
    "DevOps Engineer": {
        "required_skills": ["linux", "aws", "docker", "kubernetes", "ci/cd", "jenkins", "terraform", "bash"],
        "good_to_have": ["python", "ansible", "prometheus", "grafana", "gcp", "azure", "security"],
        "experience_keywords": ["automation", "deployment", "monitoring", "infrastructure", "iac", "scalability", "reliability"]
    },
}