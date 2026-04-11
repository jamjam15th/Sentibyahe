"""Shared helpers for comparing sentiment models (Analysis page)."""
from __future__ import annotations

import re
from typing import Any

# Underlying checkpoint for the app’s sentiment pipeline (code / weights only)
OUR_MODEL_ID = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# User-facing name in Analysis copy (replace long repo id in descriptions)
OUR_MODEL_DISPLAY_NAME = "Fine-tuned XLM-RoBERTa"

CARDIFF_3WAY_LABELS: dict[str, str] = {
    "LABEL_0": "NEGATIVE",
    "LABEL_1": "NEUTRAL",
    "LABEL_2": "POSITIVE",
    "negative": "NEGATIVE",
    "neutral": "NEUTRAL",
    "positive": "POSITIVE",
}


def normalize_comparison_prediction(kind: str, res: dict[str, Any]) -> tuple[str, float]:
    """Map pipeline output to POSITIVE / NEUTRAL / NEGATIVE."""
    lab_raw = res.get("label", "")
    sc = round(float(res.get("score", 0.0)), 4)
    if kind == "stars":
        m = re.search(r"(\d)", str(lab_raw))
        n = int(m.group(1)) if m else 3
        if n <= 2:
            return "NEGATIVE", sc
        if n >= 4:
            return "POSITIVE", sc
        return "NEUTRAL", sc
    if kind == "sst2":
        u = str(lab_raw).upper()
        if sc < 0.55:
            return "NEUTRAL", sc
        if "NEG" in u or u == "LABEL_0":
            return "NEGATIVE", sc
        return "POSITIVE", sc
    tag = CARDIFF_3WAY_LABELS.get(lab_raw)
    if tag is None:
        u = str(lab_raw).upper()
        tag = u if u in ("POSITIVE", "NEUTRAL", "NEGATIVE") else "NEUTRAL"
    return tag, sc


# Selectbox shows the real Hugging Face model id; kind drives label normalization
COMPARISON_MODEL_CHOICES: list[dict[str, str]] = [
    {
        "user_label": "Baseline — cardiffnlp/twitter-roberta-base-sentiment-latest (RoBERTa · English Twitter · 3-class)",
        "model_id": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "kind": "cardiff3",
    },
    {
        "user_label": "Baseline — nlptown/bert-base-multilingual-uncased-sentiment (BERT multilingual · stars → 3-class)",
        "model_id": "nlptown/bert-base-multilingual-uncased-sentiment",
        "kind": "stars",
    },
    {
        "user_label": "Baseline — distilbert-base-uncased-finetuned-sst-2-english (DistilBERT · SST-2 English · binary + uncertain → neutral)",
        "model_id": "distilbert-base-uncased-finetuned-sst-2-english",
        "kind": "sst2",
    },
]
