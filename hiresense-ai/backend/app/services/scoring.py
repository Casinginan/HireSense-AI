"""
AI Matching / Scoring Engine (SRS Sections 11, 14, 15, 16).

MVP scaffold note
------------------
This module implements a fully transparent, deterministic, RULE-BASED scoring engine that
mirrors the weighted formula and explanation structure specified in the SRS (Section 16),
and produces the same output shape (category breakdown, matched/missing skills, factor-level
explanation, confidence, suitability label) that a trained XGBoost model + SHAP explainer
would produce in a full production deployment (SRS Sections 14-15).

Swapping in a real ML model later only requires changing `predict_suitability()` below to
call a trained model + SHAP, without touching any API route or frontend code, because the
output schema (`ScoreResult`) is already the contract the rest of the system depends on.

No protected attributes (age, gender, race, religion, nationality, marital status,
photographs — SRS Section 18) are read, stored as features, or referenced anywhere in this
module. Only job-relevant fields (skills, experience, education, certifications, projects,
text similarity) are used.
"""
from dataclasses import dataclass, field

from app.services.skills_taxonomy import extract_skills_from_text

DEFAULT_WEIGHTS = {
    "skills": 35,
    "experience": 25,
    "education": 15,
    "certifications": 10,
    "projects": 10,
    "semantic_similarity": 5,
}

EDUCATION_RANK = {"none": 0, "unknown": 0, "associate": 1, "bachelor": 2, "master": 3, "doctorate": 4}


@dataclass
class ScoreResult:
    overall_score: float
    suitability_label: str
    confidence: float
    category_breakdown: dict
    matched_skills: list[str]
    missing_skills: list[str]
    explanation_factors: list[dict]
    recommendation_text: str
    weights_snapshot: dict = field(default_factory=dict)
    model_version: str = "rule-engine-v1.0"


def _skills_score(candidate_skills: set[str], required: list[str], preferred: list[str]) -> tuple[float, list[str], list[str]]:
    required_set = {s.lower() for s in required}
    preferred_set = {s.lower() for s in preferred}
    candidate_lower = {s.lower() for s in candidate_skills}

    matched_required = required_set & candidate_lower
    matched_preferred = preferred_set & candidate_lower
    missing_required = required_set - candidate_lower
    missing_preferred = preferred_set - candidate_lower

    if not required_set and not preferred_set:
        return 100.0, [], []

    required_ratio = (len(matched_required) / len(required_set)) if required_set else 1.0
    preferred_ratio = (len(matched_preferred) / len(preferred_set)) if preferred_set else 1.0

    # Required skills weighted more heavily than preferred within the skills category itself
    score = (required_ratio * 0.75 + preferred_ratio * 0.25) * 100
    matched = sorted(matched_required | matched_preferred)
    missing = sorted(missing_required | missing_preferred)
    return round(score, 1), matched, missing


def _experience_score(candidate_years: float, min_years: float, max_years: float) -> float:
    if max_years <= 0:
        return 100.0 if candidate_years >= min_years else 50.0
    if candidate_years < min_years:
        # Linear falloff below the minimum, floor at 20 so a near-miss isn't treated as zero
        if min_years == 0:
            return 100.0
        ratio = candidate_years / min_years
        return round(max(20.0, ratio * 100), 1)
    if candidate_years <= max_years:
        # Within range: scale from 80 (at min) to 100 (at max)
        span = max_years - min_years
        if span <= 0:
            return 100.0
        ratio = (candidate_years - min_years) / span
        return round(80 + ratio * 20, 1)
    # Above max: diminishing returns, capped near 100 to avoid over-rewarding excess experience
    excess = candidate_years - max_years
    return round(max(85.0, 100 - excess * 2), 1)


def _education_score(candidate_level: str, required_level: str) -> float:
    candidate_rank = EDUCATION_RANK.get(candidate_level, 0)
    required_rank = EDUCATION_RANK.get(required_level, 0)
    if candidate_rank >= required_rank:
        return 100.0
    gap = required_rank - candidate_rank
    return round(max(30.0, 100 - gap * 25), 1)


def _certifications_score(candidate_skills: set[str], preferred_certs: list[str]) -> float:
    if not preferred_certs:
        return 100.0
    cert_set = {c.lower() for c in preferred_certs}
    matched = cert_set & {s.lower() for s in candidate_skills}
    return round((len(matched) / len(cert_set)) * 100, 1)


def _projects_score(resume_text: str, job_description: str) -> float:
    """Lightweight keyword-overlap proxy for 'project relevance' (SRS Section 16.1)."""
    if not resume_text or not job_description:
        return 50.0
    job_words = {w.lower() for w in job_description.split() if len(w) > 4}
    resume_words = {w.lower() for w in resume_text.split() if len(w) > 4}
    if not job_words:
        return 50.0
    overlap = len(job_words & resume_words) / len(job_words)
    return round(min(100.0, overlap * 150), 1)


def _semantic_similarity_score(resume_text: str, job_description: str) -> float:
    """Jaccard word-overlap similarity as a lightweight stand-in for sentence-embedding
    cosine similarity (SRS Section 13). Swap in Sentence-Transformers + cosine similarity
    for production use — see README 'Extending the AI pipeline'."""
    if not resume_text or not job_description:
        return 0.0
    a = {w.lower().strip(".,;:()") for w in resume_text.split()}
    b = {w.lower().strip(".,;:()") for w in job_description.split()}
    if not a or not b:
        return 0.0
    jaccard = len(a & b) / len(a | b)
    return round(min(100.0, jaccard * 400), 1)


def _label_for_score(score: float, confidence: float) -> str:
    if confidence < 0.5:
        return "Needs Review"
    if score >= 85:
        return "Highly Suitable"
    if score >= 70:
        return "Suitable"
    if score >= 50:
        return "Potential Fit"
    if score >= 30:
        return "Needs Review"
    return "Not Recommended"


def _build_explanation(breakdown: dict, matched: list[str], missing_required: list[str]) -> list[dict]:
    factors = []
    sorted_categories = sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)
    for category, value in sorted_categories:
        direction = "positive" if value >= 70 else ("neutral" if value >= 50 else "negative")
        factors.append({
            "factor": category.replace("_", " ").title(),
            "value": value,
            "direction": direction,
        })
    if matched:
        factors.insert(0, {"factor": f"Matched skills: {', '.join(matched[:5])}", "value": None, "direction": "positive"})
    if missing_required:
        factors.append({"factor": f"Missing required: {', '.join(missing_required[:5])}", "value": None, "direction": "negative"})
    return factors


def _recommendation_text(label: str, breakdown: dict, missing_required: list[str]) -> str:
    weakest_category = min(breakdown, key=breakdown.get)
    if label == "Highly Suitable":
        return "Strong overall alignment with the role's stated requirements."
    if label == "Suitable":
        return f"Solid overall fit; {weakest_category.replace('_', ' ')} is comparatively the weakest area."
    if label == "Potential Fit":
        return f"Meets a meaningful subset of requirements — worth a closer manual look, particularly around {weakest_category.replace('_', ' ')}."
    if label == "Needs Review":
        return "Mixed or uncertain signals in the available data — recommend manual review before deciding."
    return f"Limited alignment with stated requirements based on available data (notably: {', '.join(missing_required[:3]) if missing_required else weakest_category.replace('_', ' ')})."


def score_application(
    *,
    candidate_skills: list[str],
    candidate_experience_years: float,
    candidate_education_level: str,
    resume_text: str,
    job_required_skills: list[str],
    job_preferred_skills: list[str],
    job_min_experience: float,
    job_max_experience: float,
    job_required_education: str,
    job_description: str,
    weights: dict | None = None,
) -> ScoreResult:
    weights = weights or DEFAULT_WEIGHTS
    candidate_skills_set = set(candidate_skills)

    skills_score, matched, missing = _skills_score(candidate_skills_set, job_required_skills, job_preferred_skills)
    experience_score = _experience_score(candidate_experience_years, job_min_experience, job_max_experience)
    education_score = _education_score(candidate_education_level, job_required_education)
    certifications_score = _certifications_score(candidate_skills_set, job_preferred_skills)
    projects_score = _projects_score(resume_text, job_description)
    semantic_score = _semantic_similarity_score(resume_text, job_description)

    breakdown = {
        "skills": skills_score,
        "experience": experience_score,
        "education": education_score,
        "certifications": certifications_score,
        "projects": projects_score,
        "semantic_similarity": semantic_score,
    }

    overall = sum(breakdown[cat] * (weights[cat] / 100) for cat in breakdown)
    overall = round(overall, 1)

    # Confidence reflects how much of the input data was actually available/usable —
    # not a claim of statistical model certainty (this is a rule engine, not a trained classifier).
    data_completeness_signals = [
        1.0 if resume_text and len(resume_text) > 100 else 0.3,
        1.0 if candidate_skills_set else 0.4,
        1.0 if candidate_education_level != "unknown" else 0.5,
    ]
    confidence = round(sum(data_completeness_signals) / len(data_completeness_signals), 2)

    label = _label_for_score(overall, confidence)
    missing_required = [s for s in missing if s in {r.lower() for r in job_required_skills}]
    explanation_factors = _build_explanation(breakdown, matched, missing_required)
    recommendation = _recommendation_text(label, breakdown, missing_required)

    return ScoreResult(
        overall_score=overall,
        suitability_label=label,
        confidence=confidence,
        category_breakdown=breakdown,
        matched_skills=matched,
        missing_skills=missing,
        explanation_factors=explanation_factors,
        recommendation_text=recommendation,
        weights_snapshot=weights,
        model_version="rule-engine-v1.0",
    )
