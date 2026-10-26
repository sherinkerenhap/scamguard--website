"""ScamGuard Random Forest ML detector.

This module provides two Random Forest classifiers:
1. Text classifier using TF-IDF features.
2. URL classifier using lexical URL features.

The models are trained by train_model.py and loaded by app.py.
"""
from __future__ import annotations

import math
import os
import re
from urllib.parse import urlparse

import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_MODEL_PATH = os.path.join(BASE_DIR, "models", "scamguard_text_random_forest.pkl")
URL_MODEL_PATH = os.path.join(BASE_DIR, "models", "scamguard_url_random_forest.pkl")

_text_model = None
_url_model = None


def load_models():
    global _text_model, _url_model
    if _text_model is None and os.path.exists(TEXT_MODEL_PATH):
        _text_model = joblib.load(TEXT_MODEL_PATH)
    if _url_model is None and os.path.exists(URL_MODEL_PATH):
        _url_model = joblib.load(URL_MODEL_PATH)
    return _text_model, _url_model


def _url_features(url: str):
    value = (url or "").strip().lower()
    parsed = urlparse(value if re.match(r"^https?://", value) else "http://" + value)
    host = parsed.netloc.split("@")[ -1].split(":")[0]
    path = parsed.path or ""
    query = parsed.query or ""
    full = value

    ip_host = bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host))
    suspicious_words = ["login", "verify", "verification", "account", "secure", "update", "bank", "payment", "reward", "prize", "confirm", "free", "wallet", "signin", "password", "kyc"]
    shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly"]

    return np.array([[
        len(full),
        len(host),
        len(path),
        len(query),
        full.count("."),
        full.count("-"),
        full.count("/"),
        full.count("@"),
        full.count("%"),
        sum(ch.isdigit() for ch in full),
        int(value.startswith("https://")),
        int(value.startswith("http://")),
        int(ip_host),
        int(any(w in full for w in suspicious_words)),
        sum(w in full for w in suspicious_words),
        int(any(s in host for s in shorteners)),
        int(len(host.split(".")) >= 4),
        int(any(x in host for x in ["xn--", "secure-login", "verify-account", "bank-login"])),
    ]], dtype=float)


def predict_text(text: str):
    model, _ = load_models()
    if model is None:
        return {"available": False, "label": "UNKNOWN", "probability": 0.0, "score": 0}

    probability = model.predict_proba([text])[0]
    classes = list(model.classes_)
    scam_index = classes.index("SPAM") if "SPAM" in classes else 1
    scam_probability = float(probability[scam_index])
    label = "SPAM" if scam_probability >= 0.50 else "HAM"
    return {
        "available": True,
        "label": label,
        "probability": round(scam_probability, 4),
        "score": int(round(scam_probability * 100)),
        "algorithm": "Random Forest",
    }


def predict_url(url: str):
    _, model = load_models()
    if model is None:
        return {"available": False, "label": "UNKNOWN", "probability": 0.0, "score": 0}

    probability = model.predict_proba(_url_features(url))[0]
    classes = list(model.classes_)
    scam_index = classes.index("SPAM") if "SPAM" in classes else 1
    scam_probability = float(probability[scam_index])
    label = "SPAM" if scam_probability >= 0.50 else "HAM"
    return {
        "available": True,
        "label": label,
        "probability": round(scam_probability, 4),
        "score": int(round(scam_probability * 100)),
        "algorithm": "Random Forest",
    }
