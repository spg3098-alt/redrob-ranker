# Redrob Intelligent Candidate Discovery — Ranker

Top-100 candidate ranker for the *Senior AI Engineer — Founding Team* job
description, over the 100,000-candidate pool in `candidates.jsonl`.

## Reproduce the submission

```bash
pip install -r requirements.txt
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
python validate_submission.py submission.csv      # -> "Submission is valid."
```

Runs in **~55 s on a CPU-only 16 GB machine, no network** — inside the spec's
5-minute budget. The ranking step makes **no external/LLM API calls** and uses
**no GPU**, per the compute constraints.

## Approach (why it beats keyword/embedding-only)

The JD is deliberately written so that "most AI keywords wins" is a trap, and
the pool contains keyword stuffers plus ~80 honeypots. We therefore translate
the JD prose into explicit, weighted scoring logic (`src/redrob_ranker/jd.py`)
rather than relying on similarity alone. Each candidate's final score is:

```
additive   = 0.22*title + 0.38*skills_trust + 0.14*semantic
           + 0.10*ml_yoe_experience + 0.08*location + 0.08*eval_text_evidence
           (+ nice-to-have bonus)

gated      = additive
           × domain_mismatch_penalty      # ×(1 - 0.45*dm) if CV/vision-heavy
           × consulting_only_penalty      # ×0.45 if entire career at services firms
           × shallow_llm_penalty          # ×0.80 if only framework calls, no IR depth
           × tenure_stability             # ×0.80–1.04 based on job-hop pattern
           × notice_multiplier            # ×0.65–1.00 by notice period days
           × junior_title_penalty         # ×0.80 if "junior" in current title
           × ml_yoe_gate                  # ×0.25/<3y, ×0.60/<4y, ×0.95/<5y
           × core_coverage_gate           # ×0.30 if 0/4 + no eval text; ×0.70 if ≤1/4
           × open_to_work_gate            # ×0.85 if not open to work
           × self_assessment_penalty      # ×0.85 if summary admits weakness

final      = gated
           × behavioral_multiplier        # ×0.40–1.28 (capped at 1.0 if coverage ≤2/4)
           × honeypot_sink                # ×0.03–0.50 for impossible profiles
```

Component highlights:

- **Title sets a ceiling** (`structured.py`). The JD's decisive negative — a
  "Marketing Manager" with a perfect skill list is *not* a fit — means a
  non-tech title is capped low regardless of listed skills. A strong *past* ML
  title can rescue an adjacent current title (e.g. ML → Backend Engineer).
- **Trust-weighted skills** (`skills.py`) defeat stuffers. Claimed proficiency
  is discounted by `skill_assessment_scores`, `endorsements`, and
  `duration_months`. "Expert" + 38/100 assessment + 0 months ≈ no credit.
  Relevance saturates, so *depth in the few groups the JD needs* (retrieval,
  vector search, ranking eval) beats *breadth across many that don't matter*.
- **Semantic layer** (`semantic.py`) catches the gem who built a recsys but
  never wrote "RAG." Uses precomputed `bge-small` embeddings if present, else
  an offline TF-IDF fallback — both CPU-only and network-free.
- **Behavioral availability** (`behavioral.py`) down-weights perfect-on-paper
  but inactive / unresponsive candidates, as the JD explicitly requests.
- **Honeypot sink** (`honeypot.py`) pushes internally-inconsistent profiles to
  the bottom via consistency checks (impossible tenures, expert-with-0-months,
  date contradictions). We *sink* rather than hard-delete, so a false positive
  can never silently drop a real candidate. Current top-100 honeypot rate: 0%.

There are **no labels** in this challenge, so this is a hand-engineered and
hand-tuned scoring function (validated by manually inspecting the top ranks
with `inspect_top.py`), not a trained model.

## Layout

```
rank.py                     # entry point — produces submission.csv
precompute_embeddings.py    # OPTIONAL offline embeddings (preferred semantic backend)
inspect_top.py              # QA: dump full profiles of your top-N
validate_submission.py      # official validator (vendored)
requirements.txt
submission_metadata.yaml
src/redrob_ranker/
  jd.py            # the JD encoded as weighted requirements
  load.py          # streaming JSONL loader
  honeypot.py      # impossible-profile detection
  skills.py        # trust-weighted skill relevance + domain mismatch
  structured.py    # title / experience / location / notice / consulting
  behavioral.py    # availability modifier
  semantic.py      # embeddings (or TF-IDF fallback) similarity to JD
  reasoning.py     # honest, specific per-candidate reasoning strings
  score.py         # combines everything
```

## Optional: higher-quality semantic backend

```bash
pip install sentence-transformers
python precompute_embeddings.py --candidates ./candidates.jsonl
# writes data/*.npy ; rank.py picks them up automatically (still CPU/offline at rank time)
```

## Notes for evaluation

- The `reasoning` column is built only from facts in each candidate's profile
  (no hallucinated skills), varies per candidate, and surfaces honest concerns.
- Tuning weights live at the top of `score.py`; thresholds in `jd.py` each map
  to a specific JD line.
