#!/usr/bin/env python3
"""
Insert synthetic form_responses so you can explore the dashboard without manual surveys.

Prerequisites
  - pip install supabase  (added to project requirements.txt)
  - Environment variables (PowerShell example):
      $env:SUPABASE_URL = "https://xxxx.supabase.co"
      $env:SUPABASE_SERVICE_ROLE_KEY = "eyJ..."   # recommended: bypasses RLS for inserts

  The anon key often cannot insert into form_responses depending on your RLS policies.
  Never commit the service role key or expose it in Streamlit client code.

Usage
  python scripts/seed_dashboard_demo.py --email you@example.com --count 25
  python scripts/seed_dashboard_demo.py --email you@example.com --clear

Rows are tagged with client_submission_id = seed-dashboard-demo-<n> so you can clear them.

Each row is enriched with standard demographics (for the Demographics tab), legacy transport
prompts where useful, synthetic SERVQUAL averages + Likert answers if your form had no scales,
and an extra open-text answer for the Sentiment feedback log.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone

from supabase import Client, create_client

SEED_PREFIX = "seed-dashboard-demo"

FEEDBACK_SNIPPETS_EXTRA = [
    "Nakakapagod mag-commute araw-araw pero kailangan talaga.",
    "Sana mas dumami ang mga bus sa umaga.",
    "The e-trike was clean; medyo mahal lang ang pamasahe.",
    "Hindi ko gets yung route ng UV, naliligaw ako.",
    "Smooth trip, walang problema sa bayad.",
    "Mainit, walang bentilasyon, pero mabilis.",
    "Drivers should slow down sa mga crossing.",
    "Salamat sa libreng sakay program, malaking tulong.",
]

FEEDBACK_SNIPPETS = [
    "Maayos naman ang byahe kahit medyo siksikan sa jeep.",
    "The driver was helpful pero ang tagal maghintay sa terminal.",
    "Sobrang init sa loob, sana i-maintain ang aircon.",
    "Okay lang overall, on time naman ang bus.",
    "Hindi maganda ang experience, mabaho at barado ang daanan.",
    "Mixed feelings — mabilis pero delikado mag-overtake.",
    "I appreciate the modern e-jeepney, mas komportable.",
    "Walang maayos na pila, nakakalito sa rush hour.",
    "Mabait ang konduktor, nagpapaalam bago magbayad.",
    "Late lagi ang schedule, nakakafrustrate for students.",
    "Taglish test: okay naman pero sana less waiting time.",
    "The fare is fair for the distance, no issues.",
    "Delikado yung pagbaba, walang designated stop.",
] + FEEDBACK_SNIPPETS_EXTRA

DEMO_OPTIONS = {
    "1. Age / Edad": ["Below / Mababa sa 18", "18-25", "26-35", "36-45", "46-55", "Above / Mataas sa 55"],
    "2. Gender / Kasarian": ["Male (Lalaki)", "Female (Babae)", "Prefer not to say (Mas pinipiling huwag sabihin)"],
    "3. Occupational Status / Katayuan sa Trabaho": ["Student (Estudyante)", "Employee / Self-employed (Empleyado / may sariling pinagkikitaan)", "Employer / Business-owner (May-ari ng Negosyo)", "Unemployed (Walang trabaho)"],
    "4. Monthly Allowance or Salary / Buwanang Sahod o Allowance": ["Below / Mababa sa Php 5,000", "Php 5,001 - 10,000", "Php 10,001 - 20,000", "Php 20,001 - 30,000", "Php 30,001 - 40,000", "Php 40,001 - 50,000", "Above / Mataas sa Php 50,001"],
    "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?": ["Once a week (Isang beses sa isang linggo)", "2-3 times a week (2-3 beses sa isang linggo)", "4-5 times a week (4-5 beses sa isang linggo)", "Everyday (Araw-araw)"],
}

TRANSPORT_MULTI = [
    "Modern jeepney (e-jeep)",
    "Traditional jeepney",
    "Bus (provincial or city)",
    "UV Express / van",
    "Tricycle (for last mile)",
]

# Dashboard also recognizes legacy profile prompts (see dashboard.TRANSPORT_DEMO_KEYS).
LEGACY_TRANSPORT_PRIMARY = "What primary land public transportation mode do you usually use?"
LEGACY_PUV_MULTI = "Which PUV or transport types do you usually ride or use? (Select all that apply)"
STANDARD_TRANSPORT_MULTI = (
    "Which land public transportation modes do you usually use? (Select all that apply)"
)

SEED_LIKERT_FOR_QUANTITATIVE = [
    ("tangibles_avg", "[Demo seed] Vehicles & facilities (Tangibles)"),
    ("reliability_avg", "[Demo seed] Timeliness & reliability (Reliability)"),
    ("responsiveness_avg", "[Demo seed] Staff responsiveness (Responsiveness)"),
    ("assurance_avg", "[Demo seed] Safety & assurance (Assurance)"),
    ("empathy_avg", "[Demo seed] Courtesy & empathy (Empathy)"),
]


def _transport_modes_for_seq(seq: int) -> list[str]:
    i = seq % len(TRANSPORT_MULTI)
    j = (seq + 2) % len(TRANSPORT_MULTI)
    if i == j:
        j = (j + 1) % len(TRANSPORT_MULTI)
    return [TRANSPORT_MULTI[i], TRANSPORT_MULTI[j]]


def enrich_response_for_dashboard(row: dict, seq: int, rng: random.Random) -> dict:
    """
    Pad demo_answers so Demographics charts always have standard columns,
    fill SERVQUAL *_avg + Likert-style answers when the form had no scales,
    and add an extra open-text key for Feedback log QA.
    """
    out = {**row}
    demo = dict(out.get("demo_answers") or {})
    ans = dict(out.get("answers") or {})

    ages = DEMO_OPTIONS["1. Age / Edad"]
    demo.setdefault("1. Age / Edad", ages[seq % len(ages)])
    genders = DEMO_OPTIONS["2. Gender / Kasarian"]
    demo.setdefault("2. Gender / Kasarian", genders[seq % len(genders)])
    occs = DEMO_OPTIONS["3. Occupational Status / Katayuan sa Trabaho"]
    demo.setdefault("3. Occupational Status / Katayuan sa Trabaho", occs[seq % len(occs)])
    commutes = DEMO_OPTIONS["5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?"]
    demo.setdefault("5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?", commutes[seq % len(commutes)])

    modes = list(demo.get(STANDARD_TRANSPORT_MULTI) or _transport_modes_for_seq(seq))
    demo.setdefault(STANDARD_TRANSPORT_MULTI, modes)
    demo.setdefault(LEGACY_PUV_MULTI, list(modes))
    if LEGACY_TRANSPORT_PRIMARY not in demo:
        demo[LEGACY_TRANSPORT_PRIMARY] = modes[0] if modes else TRANSPORT_MULTI[0]

    for k, v in demo.items():
        ans.setdefault(k, v)

    avg_cols = [
        "tangibles_avg",
        "reliability_avg",
        "responsiveness_avg",
        "assurance_avg",
        "empathy_avg",
    ]
    if all(out.get(k) is None for k in avg_cols):
        for col, qtext in SEED_LIKERT_FOR_QUANTITATIVE:
            val_f = round(rng.uniform(2.6, 4.35), 2)
            out[col] = val_f
            ans[qtext] = max(1, min(5, int(round(val_f))))
        if out.get("general_ratings_avg") is None:
            out["general_ratings_avg"] = round(rng.uniform(2.75, 4.15), 2)
        ans.setdefault(
            "[Demo seed] Overall trip satisfaction (General)",
            max(1, min(5, int(round(out["general_ratings_avg"])))),
        )

    ans.setdefault("[Demo seed] Quick follow-up (open text)", _pick_feedback_text(rng))

    out["demo_answers"] = demo
    out["answers"] = ans
    return out


def _require_env(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    if not v:
        print(f"Missing environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return v


def get_client() -> Client:
    url = _require_env("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    if not key:
        print(
            "Set SUPABASE_SERVICE_ROLE_KEY (recommended) or SUPABASE_KEY in the environment.",
            file=sys.stderr,
        )
        sys.exit(1)
    return create_client(url, key)


def clear_seed_rows(client: Client, admin_email: str) -> int:
    res = (
        client.table("form_responses")
        .select("id,client_submission_id")
        .eq("admin_email", admin_email)
        .execute()
    )
    rows = res.data or []
    ids = [
        r["id"]
        for r in rows
        if str(r.get("client_submission_id") or "").startswith(SEED_PREFIX)
    ]
    if not ids:
        return 0
    client.table("form_responses").delete().in_("id", ids).execute()
    return len(ids)


def _unique_answer_keys(questions: list[dict]) -> list[tuple[str, dict]]:
    """Match public_form: answer dict keys use disambiguated prompts."""
    answers_keys: dict[str, None] = {}
    out: list[tuple[str, dict]] = []
    for q in questions:
        prompt = (q.get("prompt") or "").strip()
        up = prompt
        n = 1
        while up in answers_keys:
            up = f"{prompt} ({n})"
            n += 1
        answers_keys[up] = None
        out.append((up, q))
    return out


def _pick_feedback_text(rng: random.Random) -> str:
    return rng.choice(FEEDBACK_SNIPPETS)


def _sentiment_for_text(text: str, rng: random.Random) -> tuple[str, float]:
    tlow = text.lower()
    if any(w in tlow for w in ("hindi", "delikado", "frustrat", "mabaho", "walang", "late lagi")):
        return "NEGATIVE", round(rng.uniform(0.72, 0.93), 4)
    if any(w in tlow for w in ("okay", "maayos", "appreciate", "fair", "komportable", "mabait")):
        return "POSITIVE", round(rng.uniform(0.75, 0.96), 4)
    return "NEUTRAL", round(rng.uniform(0.55, 0.82), 4)


def build_payload(
    public_id: str,
    admin_email: str,
    seq: int,
    created_at: datetime,
    keyed_questions: list[tuple[str, dict]],
    rng: random.Random,
) -> dict:
    answers: dict = {}
    demo_answers: dict = {}
    raw_feedback_list: list[str] = []
    dim_scores = {
        "Tangibles": [],
        "Reliability": [],
        "Responsiveness": [],
        "Assurance": [],
        "Empathy": [],
    }
    general_ratings: list[int] = []

    for uprompt, q in keyed_questions:
        q_type = q.get("q_type") or ""
        dim = q.get("servqual_dimension")
        is_demo = bool(q.get("is_demographic")) or dim == "Commuter Profile"
        opts = q.get("options") or []
        scale_max = int(q.get("scale_max") or 5)

        if q_type in ("Rating (Likert)", "Rating (1-5)"):
            val = rng.randint(1, max(2, scale_max))
            answers[uprompt] = val
            if is_demo:
                demo_answers[q["prompt"]] = val
            elif dim in dim_scores:
                dim_scores[dim].append(val)
            else:
                general_ratings.append(val)
        elif q_type == "Multiple Choice":
            if opts:
                choice = rng.choice(opts)
            else:
                choice = "Option A"
            answers[uprompt] = choice
            if is_demo:
                demo_answers[q["prompt"]] = choice
        elif q_type == "Multiple Select":
            if len(opts) >= 2:
                k = rng.randint(1, min(3, len(opts)))
                picked = rng.sample(opts, k=k)
            elif len(opts) == 1:
                picked = [opts[0]]
            else:
                picked = [rng.choice(TRANSPORT_MULTI)]
            answers[uprompt] = picked
            if is_demo:
                demo_answers[q["prompt"]] = picked
        elif q_type in ("Short Answer", "Paragraph"):
            text = _pick_feedback_text(rng) if not is_demo else rng.choice(["—", "N/A", "See above"])
            answers[uprompt] = text
            if is_demo:
                demo_answers[q["prompt"]] = text
            else:
                # Same rule as public_form: open text feeds raw_feedback
                raw_feedback_list.append(str(text))
        else:
            answers[uprompt] = "—"

    if not raw_feedback_list:
        raw_feedback_list.append(_pick_feedback_text(rng))

    combined_feedback = " | ".join(raw_feedback_list)
    sentiment_label, sentiment_score = _sentiment_for_text(combined_feedback, rng)

    def avg(xs: list[int]) -> float | None:
        return sum(xs) / len(xs) if xs else None

    return {
        "public_id": public_id,
        "admin_email": admin_email,
        "client_submission_id": f"{SEED_PREFIX}-{seq}",
        "answers": answers,
        "demo_answers": demo_answers,
        "raw_feedback": " | ".join(raw_feedback_list),
        "sentiment_status": sentiment_label,
        "sentiment_score": sentiment_score,
        "tangibles_avg": avg(dim_scores["Tangibles"]),
        "reliability_avg": avg(dim_scores["Reliability"]),
        "responsiveness_avg": avg(dim_scores["Responsiveness"]),
        "assurance_avg": avg(dim_scores["Assurance"]),
        "empathy_avg": avg(dim_scores["Empathy"]),
        "general_ratings_avg": avg(general_ratings) if general_ratings else None,
        "created_at": created_at.replace(tzinfo=timezone.utc).isoformat(),
    }


def build_minimal_payload(
    public_id: str,
    admin_email: str,
    seq: int,
    created_at: datetime,
    rng: random.Random,
) -> dict:
    """Used when there are no rows in form_questions (dashboard still populates)."""
    text = _pick_feedback_text(rng)
    sentiment_label, sentiment_score = _sentiment_for_text(text, rng)
    ages = DEMO_OPTIONS["1. Age / Edad"]
    genders = DEMO_OPTIONS["2. Gender / Kasarian"]
    occs = DEMO_OPTIONS["3. Occupational Status / Katayuan sa Trabaho"]
    commutes = DEMO_OPTIONS["5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?"]
    demo_answers = {
        "1. Age / Edad": ages[seq % len(ages)],
        "2. Gender / Kasarian": genders[seq % len(genders)],
        "3. Occupational Status / Katayuan sa Trabaho": occs[seq % len(occs)],
        STANDARD_TRANSPORT_MULTI: _transport_modes_for_seq(seq),
        "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?": commutes[seq % len(commutes)],
    }
    answers = {
        **{k: v for k, v in demo_answers.items()},
        "[Demo] Rate overall vehicle condition (Tangibles)": rng.randint(1, 5),
        "[Demo] Rate schedule reliability (Reliability)": rng.randint(1, 5),
        "[Demo] Rate staff responsiveness (Responsiveness)": rng.randint(1, 5),
        "[Demo] Rate feeling safe on board (Assurance)": rng.randint(1, 5),
        "[Demo] Rate driver courtesy (Empathy)": rng.randint(1, 5),
        "[Demo] Overall trip satisfaction (General)": rng.randint(1, 5),
        "[Demo] Open feedback about your last land public transportation trip": text,
    }
    tang = [answers["[Demo] Rate overall vehicle condition (Tangibles)"]]
    rel = [answers["[Demo] Rate schedule reliability (Reliability)"]]
    resp = [answers["[Demo] Rate staff responsiveness (Responsiveness)"]]
    assu = [answers["[Demo] Rate feeling safe on board (Assurance)"]]
    empa = [answers["[Demo] Rate driver courtesy (Empathy)"]]
    gen = [answers["[Demo] Overall trip satisfaction (General)"]]

    return {
        "public_id": public_id,
        "admin_email": admin_email,
        "client_submission_id": f"{SEED_PREFIX}-{seq}",
        "answers": answers,
        "demo_answers": demo_answers,
        "raw_feedback": text,
        "sentiment_status": sentiment_label,
        "sentiment_score": sentiment_score,
        "tangibles_avg": sum(tang) / len(tang),
        "reliability_avg": sum(rel) / len(rel),
        "responsiveness_avg": sum(resp) / len(resp),
        "assurance_avg": sum(assu) / len(assu),
        "empathy_avg": sum(empa) / len(empa),
        "general_ratings_avg": sum(gen) / len(gen),
        "created_at": created_at.replace(tzinfo=timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo dashboard data in form_responses.")
    parser.add_argument("--email", required=True, help="Researcher admin_email (same as login).")
    parser.add_argument("--count", type=int, default=20, help="Number of synthetic responses (default 20).")
    parser.add_argument("--clear", action="store_true", help="Remove previous seed rows for this email, then exit.")
    parser.add_argument(
        "--force-minimal",
        action="store_true",
        help="Insert canned rows even if form_questions is empty (uses [Demo] prompts in answers).",
    )
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible data.")
    args = parser.parse_args()

    client = get_client()
    admin_email = args.email.strip()

    removed = clear_seed_rows(client, admin_email)
    if args.clear:
        print(f"Removed {removed} seed row(s) for {admin_email}.")
        return

    meta_res = (
        client.table("form_meta").select("*").eq("admin_email", admin_email).limit(1).execute()
    )
    meta_rows = meta_res.data or []
    if not meta_rows:
        print(
            "No form_meta row for this email. Open Form Builder once while logged in as this user, then retry.",
            file=sys.stderr,
        )
        sys.exit(1)
    public_id = meta_rows[0].get("public_id")
    if not public_id:
        print("form_meta is missing public_id.", file=sys.stderr)
        sys.exit(1)

    q_res = (
        client.table("form_questions")
        .select("*")
        .eq("admin_email", admin_email)
        .order("sort_order")
        .execute()
    )
    questions = q_res.data or []

    if not questions and not args.force_minimal:
        print(
            "No questions in form_questions. Add questions in Form Builder, or re-run with --force-minimal.",
            file=sys.stderr,
        )
        sys.exit(1)

    rng = random.Random(args.seed)
    now = datetime.now(timezone.utc)
    batch: list[dict] = []

    for i in range(args.count):
        days_ago = rng.randint(0, 28)
        hour = rng.randint(8, 20)
        minute = rng.randint(0, 59)
        created = now - timedelta(days=days_ago)
        created = created.replace(hour=hour, minute=minute, second=rng.randint(0, 59), microsecond=0)

        if questions:
            kq = _unique_answer_keys(questions)
            row = build_payload(public_id, admin_email, i, created, kq, rng)
        else:
            row = build_minimal_payload(public_id, admin_email, i, created, rng)
        batch.append(enrich_response_for_dashboard(row, i, rng))

    client.table("form_responses").insert(batch).execute()
    print(
        f"Inserted {len(batch)} demo response(s) for {admin_email}. "
        f"Open the Dashboard (date range ~last 30 days). Clear with: --clear"
    )


if __name__ == "__main__":
    main()
