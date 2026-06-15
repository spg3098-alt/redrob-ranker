"""
score.py — Combine all components into one fit score per candidate.

v2 changes:
  - Rebalanced weights: skills up to 0.38, explicit eval-text slice (0.08),
    notice moved out of additive blend into a multiplicative gate.
  - Eval-framework language in prose (NDCG/MRR/A-B test) now directly scored.
  - Notice penalty now multiplicative so it has real teeth.
"""

from typing import Dict, Any, Tuple
from . import structured, skills, behavioral, honeypot, reasoning

# HOQ-derived weights (sum to 1.0).
W_TITLE      = 0.22
W_SKILLS     = 0.38
W_SEMANTIC   = 0.14
W_EXPERIENCE = 0.10
W_LOCATION   = 0.08
W_EVAL_TEXT  = 0.08


def score_candidate(c: Dict[str, Any], semantic_sim: float
                    ) -> Tuple[float, str, Dict[str, Any]]:
    t_fit, t_class = structured.title_fit(c)
    rel, strong, rel_detail = skills.relevance(c)
    exp = structured.experience_fit(c)
    loc, loc_note = structured.location_fit(c)
    _, nd = structured.notice_fit(c)
    eval_text = structured.eval_text_evidence(c)

    base = (
        W_TITLE      * t_fit
        + W_SKILLS   * rel
        + W_SEMANTIC * semantic_sim
        + W_EXPERIENCE * exp
        + W_LOCATION * loc
        + W_EVAL_TEXT * eval_text
    )
    base += structured.nice_to_have_bonus(c)

    # Gates / penalties (multiplicative).
    dm = skills.domain_mismatch(c)
    if dm:
        base *= (1.0 - 0.45 * dm)
    cons = structured.consulting_penalty(c)
    base *= cons
    if structured.shallow_llm_flag(c):
        base *= 0.8
        shallow = True
    else:
        shallow = False

    ten_mult, n_short, avg_ten = structured.tenure_stability(c)
    base *= ten_mult
    bt_mult, bt_only = structured.big_tech_only(c)
    base *= bt_mult

    notice_mult = structured.notice_multiplier(c)
    base *= notice_mult

    behav_mult, behav_note = behavioral.modifier(c)
    base *= behav_mult

    hp = honeypot.suspicion(c)
    if hp >= 0.6:
        base *= 0.03
    elif hp >= 0.3:
        base *= 0.5

    final = max(0.0, base)

    parts = {
        "strong_skills": strong, "title_class": t_class,
        "rescued": t_class in ("adjacent", "other_tech") and t_fit > 0.5,
        "loc_note": loc_note, "behav_note": behav_note, "notice_days": nd,
        "notice_mult": notice_mult, "eval_text": eval_text,
        "domain_mismatch": dm, "consulting_mult": cons, "honeypot": hp,
        "shallow_llm": shallow, "core_cov": rel_detail["core_cov"],
        "assess_mag": rel_detail["assess_mag"], "n_short": n_short,
        "avg_tenure": avg_ten, "big_tech_only": bt_only,
        "company": c.get("profile", {}).get("current_company", ""),
        "title": c.get("profile", {}).get("current_title", ""),
    }
    reason = reasoning.build(c, parts)
    return final, reason, parts
