"""
Resume parsing pipeline (SRS Section 12): Upload -> Text Extraction -> Cleaning ->
Section Detection -> Skill Extraction -> Experience Calculation -> Candidate Profile.

For the MVP scaffold, OCR for scanned/image-only PDFs is out of scope (would require a
Tesseract system dependency); unsupported/unreadable files are flagged for manual entry
instead of silently failing, consistent with the SRS's edge-case handling requirement.
"""
import io
import re
from dataclasses import dataclass, field

import pdfplumber
import docx

from app.services.skills_taxonomy import extract_skills_from_text

EDUCATION_KEYWORDS = {
    "doctorate": ["phd", "ph.d", "doctorate", "doctoral"],
    "master": ["master of", "m.s.", "msc", "mba", "master's"],
    "bachelor": ["bachelor", "b.s.", "bsc", "b.a.", "undergraduate degree", "bachelor's"],
    "associate": ["associate degree", "associate's"],
}

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:\b\d{4}\b)|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4})"
    r"\s*(?:-|to|–|—)\s*"
    r"(?P<end>present|current|now|(?:\b\d{4}\b)|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4})",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?){2,4}\d{3,4}")


@dataclass
class ParsedResume:
    raw_text: str
    full_name_guess: str | None
    email: str | None
    phone: str | None
    skills: list[str] = field(default_factory=list)
    total_experience_years: float = 0.0
    highest_education_level: str = "unknown"
    confidence: float = 0.0


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def guess_full_name(text: str) -> str | None:
    """Heuristic: the first non-empty line that looks like a name (2-4 capitalized words,
    no digits/@) is very likely the candidate's name at the top of a resume."""
    for line in text.splitlines()[:8]:
        line = line.strip()
        if not line or "@" in line or any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0:1].isupper() for w in words if w):
            return line
    return None


def detect_education_level(text: str) -> str:
    lowered = text.lower()
    for level in ("doctorate", "master", "bachelor", "associate"):
        for kw in EDUCATION_KEYWORDS[level]:
            if kw in lowered:
                return level
    return "unknown"


def calculate_experience_years(text: str) -> float:
    """Sums non-overlapping date ranges found in the resume text. This is a simplified,
    deterministic heuristic for the MVP scaffold — production systems should resolve
    overlapping concurrent roles more carefully (SRS Section 12 edge cases)."""
    import datetime

    current_year = datetime.date.today().year
    ranges = []
    for match in DATE_RANGE_PATTERN.finditer(text):
        start_raw = match.group("start")
        end_raw = match.group("end")
        start_year = _extract_year(start_raw)
        end_year = current_year if end_raw.lower() in ("present", "current", "now") else _extract_year(end_raw)
        if start_year and end_year and end_year >= start_year:
            ranges.append((start_year, end_year))

    if not ranges:
        return 0.0

    # Merge overlapping ranges so overlapping roles aren't double-counted
    ranges.sort()
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    total_years = sum(end - start for start, end in merged)
    return float(min(total_years, 40))  # cap to limit outlier influence (Section 14.4)


def _extract_year(text: str) -> int | None:
    m = re.search(r"\d{4}", text)
    return int(m.group(0)) if m else None


def parse_resume_file(file_bytes: bytes, filename: str) -> ParsedResume:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_bytes)
    elif lower_name.endswith(".docx"):
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")

    raw_text = clean_text(raw_text)

    if len(raw_text) < 30:
        # Likely a scanned/image-based document with no extractable text layer (would need OCR).
        return ParsedResume(
            raw_text=raw_text,
            full_name_guess=None,
            email=None,
            phone=None,
            skills=[],
            total_experience_years=0.0,
            highest_education_level="unknown",
            confidence=0.1,
        )

    email_match = EMAIL_PATTERN.search(raw_text)
    phone_match = PHONE_PATTERN.search(raw_text)

    parsed = ParsedResume(
        raw_text=raw_text,
        full_name_guess=guess_full_name(raw_text),
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0).strip() if phone_match else None,
        skills=extract_skills_from_text(raw_text),
        total_experience_years=calculate_experience_years(raw_text),
        highest_education_level=detect_education_level(raw_text),
        confidence=0.85,
    )
    return parsed
