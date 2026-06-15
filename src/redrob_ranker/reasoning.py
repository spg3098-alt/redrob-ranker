"""reasoning.py — Generate specific, differentiated, honest reasoning strings."""

from typing import Dict, Any, List


def build(c: Dict[str, Any], parts: Dict[str, Any]) -> str:
    p = c.get("profile", {})
    title = parts.get("title") or "Candidate"
    company = parts.get("company") or "?"
    yoe = p.get("years_of_experience", 0) or 0
    ml_yoe = parts.get("ml_yoe", yoe)

    yoe_str = f"{yoe:.1f} yrs total"
    if ml_yoe < yoe - 1.5:
        yoe_str += f" ({ml_yoe:.1f} yrs ML-relevant)"

    seg: List[str] = [f"{title} at {company}, {yoe_str}"]

    cov = parts.get("core_cov", 0)
    strong = parts.get("strong_skills", [])
    if strong:
        seg.append(f"covers {cov}/4 must-have areas via {', '.join(strong[:3])}")
    else:
        seg.append("no verified retrieval/ranking depth")

    et = parts.get("eval_text", 0)
    if et >= 0.67:
        seg.append("explicit eval-framework evidence (NDCG/MRR/A-B test) in profile")
    elif et >= 0.33:
        seg.append("some eval-framework language in profile")

    am = parts.get("assess_mag", 0)
    if am >= 0.8:
        seg.append("high verified assessment scores")
    elif am and am < 0.45 and strong:
        seg.append("but assessment scores are weak")

    avg_ten = parts.get("avg_tenure", 0)
    if parts.get("n_short", 0) >= 2 and avg_ten and avg_ten < 2.2:
        seg.append(f"frequent short stints (~{avg_ten:.1f}y avg)")
    elif avg_ten and avg_ten >= 3.0:
        seg.append(f"stable tenure (~{avg_ten:.1f}y avg)")

    if parts.get("title_class") == "adjacent" and parts.get("rescued"):
        seg.append("adjacent current title but career shows real ML/IR work")

    ln = parts.get("loc_note")
    loc_phrase = {
        "preferred-city": f"based in {p.get('location')}",
        "india-other-will-relocate": "open to relocating within India",
        "india-other-no-relocate": f"in {p.get('location')}, not relocating",
        "abroad-will-relocate": "abroad but open to relocating",
        "abroad-no-relocate": "abroad and not relocating (no visa sponsorship)",
    }.get(ln)
    if loc_phrase:
        seg.append(loc_phrase)

    concerns: List[str] = []
    if parts.get("behav_note"):
        concerns.append(parts["behav_note"])
    nd = parts.get("notice_days")
    nm = parts.get("notice_mult", 1.0)
    if nd and nd > 60:
        concerns.append(f"notice {nd}d (×{nm:.2f} penalty)")
    if parts.get("domain_mismatch", 0) >= 0.6:
        concerns.append("CV/speech-heavy, light NLP/IR")
    if parts.get("consulting_mult", 1.0) < 0.7:
        concerns.append("services-only career")
    if parts.get("big_tech_only"):
        concerns.append("entire career at big tech (JD prefers scrappy/product)")
    if parts.get("honeypot", 0) >= 0.6:
        concerns.append("profile consistency flags")
    if parts.get("shallow_llm"):
        concerns.append("LLM exposure looks framework-only")

    text = "; ".join(seg)
    if concerns:
        text += ". Concerns: " + ", ".join(concerns)
    return text + "."
