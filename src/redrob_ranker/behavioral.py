"""
behavioral.py — Availability / engagement modifier.

v3: Replaced 13 stacked independent multipliers with 5 composite scores.
Correlated signals (e.g. response_rate × response_time) previously
double-counted the same underlying capability. Now grouped by what they
actually measure, blended once, then mapped to a multiplier.

  Composite          Signals                               Weight
  ─────────────────  ────────────────────────────────────  ──────
  Responsiveness     response_rate, response_time           25%
  Recruiter demand   saved_by, search_appearance, views     20%
  Availability       last_active, open_to_work, apps_30d   20%
  Closability        interview_completion, offer_accept     20%
  Profile trust      verified_*, completeness_score         15%

Multiplier range: [0.40, 1.28]
"""

from datetime import date
from typing import Dict, Any, Tuple

AS_OF = date(2026, 5, 20)


def _parse(d):
    try:
        return date.fromisoformat(d)
    except Exception:
        return None


def _responsiveness(sig: dict) -> float:
    rr = sig.get("recruiter_response_rate")
    base = rr if rr is not None else 0.50
    art = sig.get("avg_response_time_hours")
    if art is not None:
        if art <= 6:     time_f = 1.15
        elif art <= 12:  time_f = 1.07
        elif art <= 48:  time_f = 1.00
        elif art <= 120: time_f = 0.92
        else:            time_f = 0.82
        base = min(base * time_f, 1.0)
    return base


def _recruiter_demand(sig: dict) -> float:
    saved  = min((sig.get("saved_by_recruiters_30d", 0) or 0) / 50.0,  1.0)
    views  = min((sig.get("profile_views_received_30d", 0) or 0) / 300.0, 1.0)
    search = min((sig.get("search_appearance_30d", 0) or 0) / 1000.0, 1.0)
    return 0.55 * saved + 0.25 * views + 0.20 * search


def _availability(sig: dict) -> float:
    la = _parse(sig.get("last_active_date", ""))
    if la:
        days = (AS_OF - la).days
        if days <= 14:    recency = 1.00
        elif days <= 45:  recency = 0.85
        elif days <= 120: recency = 0.60
        else:             recency = 0.25
    else:
        recency = 0.50
    otw  = 1.0 if sig.get("open_to_work_flag") else 0.25
    apps = min((sig.get("applications_submitted_30d", 0) or 0) / 10.0, 1.0)
    return 0.45 * recency + 0.35 * otw + 0.20 * apps


def _closability(sig: dict) -> float:
    icr = sig.get("interview_completion_rate")
    icr_score = icr if icr is not None else 0.50
    oar = sig.get("offer_acceptance_rate")
    oar_score = oar if (oar is not None and oar >= 0) else 0.50
    return 0.55 * icr_score + 0.45 * oar_score


def _trust(sig: dict) -> float:
    pcs = (sig.get("profile_completeness_score", 50) or 0) / 100.0
    verified = sum(bool(sig.get(k)) for k in
                   ("verified_email", "verified_phone", "linkedin_connected"))
    return 0.55 * pcs + 0.45 * (verified / 3.0)


W_RESPONSIVENESS   = 0.25
W_RECRUITER_DEMAND = 0.20
W_AVAILABILITY     = 0.20
W_CLOSABILITY      = 0.20
W_TRUST            = 0.15

MULT_LOW  = 0.40
MULT_HIGH = 1.28


def modifier(c: Dict[str, Any]) -> Tuple[float, str]:
    sig = c.get("redrob_signals", {}) or {}

    resp  = _responsiveness(sig)
    dem   = _recruiter_demand(sig)
    avail = _availability(sig)
    close = _closability(sig)
    trust = _trust(sig)

    composite = (
        W_RESPONSIVENESS   * resp
        + W_RECRUITER_DEMAND * dem
        + W_AVAILABILITY     * avail
        + W_CLOSABILITY      * close
        + W_TRUST            * trust
    )

    mult = MULT_LOW + composite * (MULT_HIGH - MULT_LOW)

    notes = []
    rr = sig.get("recruiter_response_rate")
    if rr is not None and rr < 0.20:
        notes.append(f"low response rate {rr:.2f}")
    la = _parse(sig.get("last_active_date", ""))
    if la and (AS_OF - la).days > 120:
        notes.append(f"inactive {(AS_OF - la).days}d")
    icr = sig.get("interview_completion_rate")
    if icr is not None and icr < 0.40:
        notes.append(f"low interview show {icr:.2f}")

    note = f"behavioral={composite:.2f} [resp={resp:.2f} dem={dem:.2f} avail={avail:.2f} close={close:.2f} trust={trust:.2f}]"
    if notes:
        note += "; " + ", ".join(notes)

    return mult, note
