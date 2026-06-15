"""
structured.py — Structured (non-text) fit components derived from the JD.
"""

from typing import Dict, Any, Tuple, List
from . import jd


def title_fit(c: Dict[str, Any]) -> Tuple[float, str]:
    p = c.get("profile", {})
    cur = p.get("current_title", "").lower()
    hist = [r.get("title", "").lower() for r in c.get("career_history", [])]

    def classify(t: str) -> str:
        if any(x in t for x in jd.CORE_TITLE_TERMS):   return "core"
        if any(x in t for x in jd.DATA_SCIENCE_TERMS):  return "data_science"
        if any(x in t for x in jd.ADJACENT_TECH_TERMS): return "adjacent"
        if any(x in t for x in jd.OTHER_TECH_TERMS):    return "other_tech"
        return "non_tech"

    cur_class = classify(cur)
    cur_score = jd.TITLE_SCORE[cur_class]
    hist_best = max((jd.TITLE_SCORE[classify(t)] for t in hist), default=0.0)
    if cur_class in ("adjacent", "other_tech"):
        score = max(cur_score, 0.75 * hist_best)
    elif cur_class == "non_tech":
        score = cur_score
    else:
        score = cur_score
    return score, cur_class


_ML_TITLE_TERMS = (
    jd.CORE_TITLE_TERMS + jd.DATA_SCIENCE_TERMS
    + ["search engineer", "ranking", "recommendation", "recsys",
       "nlp engineer", "applied scientist", "applied ml"]
)


def ml_relevant_yoe(c: Dict[str, Any]) -> float:
    """Sum duration_months only from ML/AI/IR-titled roles."""
    total_months = sum(
        r.get("duration_months", 0) or 0
        for r in c.get("career_history", [])
        if any(t in r.get("title", "").lower() for t in _ML_TITLE_TERMS)
    )
    years = total_months / 12.0
    stated = c.get("profile", {}).get("years_of_experience", 0) or 0
    return years if years > 0 else stated


def experience_fit(c: Dict[str, Any]) -> float:
    """JD: range 5-9, IDEAL 6-8. Uses ML-relevant YoE, not total career."""
    y = ml_relevant_yoe(c)
    if y < 2:   return 0.20
    if y < 4:   return 0.50
    if y < 5:   return 0.74
    if y < 6:   return 0.90
    if y <= 8:  return 1.00
    if y <= 9:  return 0.92
    if y <= 12: return 0.78
    if y <= 15: return 0.55
    return 0.38


def location_fit(c: Dict[str, Any]) -> Tuple[float, str]:
    p = c.get("profile", {})
    loc = p.get("location", "").lower()
    sig = c.get("redrob_signals", {}) or {}
    relo = sig.get("willing_to_relocate", False)
    mode = sig.get("preferred_work_mode", "")
    country = p.get("country", "").lower()

    if country == "india":
        if any(city in loc for city in jd.PREFERRED_CITIES):
            return 1.0, "preferred-city"
        if relo:
            return 0.88, "india-other-will-relocate"
        return (0.58 if mode == "remote" else 0.66), "india-other-no-relocate"
    if relo:
        return 0.45, "abroad-will-relocate"
    return 0.10, "abroad-no-relocate"


def tenure_stability(c: Dict[str, Any]) -> Tuple[float, int, float]:
    hist = c.get("career_history", [])
    completed = [h for h in hist if not h.get("is_current")]
    if len(completed) < 2:
        return 1.0, 0, 0.0
    durs = [(h.get("duration_months", 0) or 0) / 12.0 for h in completed]
    avg = sum(durs) / len(durs)
    short = sum(1 for d in durs if d < 1.5)
    if short >= 3 and avg < 1.8: return 0.80, short, avg
    if short >= 2 and avg < 2.2: return 0.90, short, avg
    if avg >= 3.0:               return 1.04, short, avg
    return 1.0, short, avg


BIG_TECH = ["google", "meta", "facebook", "apple", "amazon", "microsoft", "netflix"]
BIG_TECH_PENALTY = 0.98


def big_tech_only(c: Dict[str, Any]) -> Tuple[float, bool]:
    hist = c.get("career_history", [])
    if len(hist) < 2: return 1.0, False
    companies = [h.get("company", "").lower() for h in hist]
    if all(any(b in co for b in BIG_TECH) for co in companies):
        return BIG_TECH_PENALTY, True
    return 1.0, False


def notice_fit(c: Dict[str, Any]) -> Tuple[float, int]:
    nd = (c.get("redrob_signals", {}) or {}).get("notice_period_days", 60) or 0
    if nd <= 30: return 1.0, nd
    if nd <= 60: return 0.85, nd
    if nd <= 90: return 0.60, nd
    return 0.40, nd


def notice_multiplier(c: Dict[str, Any]) -> float:
    """Multiplicative notice penalty — moves from additive to gate."""
    nd = (c.get("redrob_signals", {}) or {}).get("notice_period_days", 60) or 0
    if nd <= 15:  return 1.00
    if nd <= 30:  return 0.97
    if nd <= 45:  return 0.93
    if nd <= 60:  return 0.88
    if nd <= 90:  return 0.80
    if nd <= 120: return 0.72
    return 0.65


def consulting_penalty(c: Dict[str, Any]) -> float:
    hist = c.get("career_history", [])
    if not hist: return 1.0
    companies = [r.get("company", "").lower() for r in hist]
    n_consult = sum(1 for co in companies
                    if any(f in co for f in jd.CONSULTING_FIRMS))
    if n_consult == len(companies) and len(companies) >= 2: return 0.45
    if n_consult == len(companies): return 0.65
    return 1.0


def nice_to_have_bonus(c: Dict[str, Any]) -> float:
    bonus = 0.0
    sig = c.get("redrob_signals", {}) or {}
    text = " ".join(s.get("name", "").lower() for s in c.get("skills", []))
    if any(x in text for x in ("lora", "qlora", "peft")): bonus += 0.02
    if any(x in text for x in ("learning to rank", "ltr", "xgboost")): bonus += 0.02
    gh = sig.get("github_activity_score", -1)
    if gh and gh > 50: bonus += 0.02
    return min(bonus, 0.06)


def eval_text_evidence(c: Dict[str, Any]) -> float:
    """Scan summary + career descriptions for explicit eval-framework language."""
    texts = (
        [c.get("profile", {}).get("summary", "").lower()]
        + [r.get("description", "").lower() for r in c.get("career_history", [])]
    )
    full = " ".join(texts)
    hits = sum(1 for t in jd.EVAL_TEXT_TERMS if t in full)
    return min(hits / 3.0, 1.0)


def shallow_llm_flag(c: Dict[str, Any]) -> bool:
    text = " ".join(
        [c.get("profile", {}).get("summary", "").lower()]
        + [r.get("description", "").lower() for r in c.get("career_history", [])]
        + [s.get("name", "").lower() for s in c.get("skills", [])]
    )
    framework = any(x in text for x in jd.FRAMEWORK_ENTHUSIAST_TERMS)
    deep = any(x in text for x in ("retrieval", "ranking", "embedding",
                                   "recommendation", "vector", "ndcg"))
    return framework and not deep
