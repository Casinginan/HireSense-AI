"""
Canonical skills taxonomy.

This is a deliberately small, curated starter list for the MVP scaffold. In a production
deployment this would live in the `skills` database table (see app/models/job.py) and be
maintained by administrators, with unmatched terms surfaced for review (Section 12 / 18 of
the SRS). Matching is case-insensitive substring/word matching for demonstration purposes;
swap in a proper NLP-based extractor (spaCy phrase matcher, embeddings) for production use.
"""

CANONICAL_SKILLS = [
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "php", "ruby", "kotlin", "swift",
    # Frontend
    "react", "next.js", "vue", "angular", "html", "css", "tailwind css", "redux", "zustand",
    # Backend
    "fastapi", "django", "flask", "node.js", "express", "spring boot", "rest api", "graphql",
    # Data / ML
    "sql", "postgresql", "mysql", "mongodb", "redis", "pandas", "numpy", "scikit-learn", "xgboost",
    "tensorflow", "pytorch", "nlp", "machine learning", "data analysis", "power bi", "tableau",
    # DevOps / Infra
    "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "github actions", "terraform", "linux",
    # General / Soft
    "project management", "agile", "scrum", "communication", "leadership", "problem solving",
    # Security
    "cybersecurity", "penetration testing", "network security", "owasp",
]

# Normalize once for fast lookup
CANONICAL_SKILLS_SET = {s.lower() for s in CANONICAL_SKILLS}


def extract_skills_from_text(text: str) -> list[str]:
    """Return canonical skill names found in the given free text (case-insensitive)."""
    if not text:
        return []
    lowered = text.lower()
    found = []
    for skill in CANONICAL_SKILLS:
        if skill.lower() in lowered:
            found.append(skill)
    return found
