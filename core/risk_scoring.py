from typing import Dict

def compute_risk_score(answers: Dict[str, int]) -> int:
    """
    answers: dict of question_id -> score (0-10 for each question)
    Returns a total risk score between 0 and 100.
    """
    if not answers:
        return 50  # neutral default

    total = sum(answers.values())
    max_total = len(answers) * 10
    normalized = int((total / max_total) * 100)
    return normalized


def classify_risk(score: int) -> str:
    """
    Convert risk score into category: 'Low', 'Medium', 'High'
    """
    if score < 35:
        return "Low"
    elif score < 70:
        return "Medium"
    else:
        return "High"

