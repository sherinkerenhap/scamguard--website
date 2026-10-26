"""
ScamGuard Random Forest Model Accuracy Evaluation

This program evaluates:
1. SMS/Text Random Forest model
2. URL Random Forest model

Metrics:
- Accuracy
- Precision
- Recall
- F1-Score
- Confusion Matrix
"""

import numpy as np
import re
from urllib.parse import urlparse

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Import training data
from train_model import (
    SPAM_TEXTS,
    HAM_TEXTS,
    SPAM_URLS,
    HAM_URLS
)


# ============================================================
# URL FEATURE EXTRACTION
# ============================================================

def url_features(url):
    value = (url or "").strip().lower()

    parsed = urlparse(
        value if re.match(r"^https?://", value)
        else "http://" + value
    )

    host = parsed.netloc.split("@")[-1].split(":")[0]
    path = parsed.path or ""
    query = parsed.query or ""

    suspicious_words = [
        "login", "verify", "verification",
        "account", "secure", "update",
        "bank", "payment", "reward",
        "prize", "confirm", "free",
        "wallet", "signin", "password", "kyc"
    ]

    shorteners = [
        "bit.ly", "tinyurl.com",
        "t.co", "goo.gl",
        "is.gd", "ow.ly"
    ]

    return [
        len(value),
        len(host),
        len(path),
        len(query),
        value.count("."),
        value.count("-"),
        value.count("/"),
        value.count("@"),
        value.count("%"),
        sum(ch.isdigit() for ch in value),
        int(value.startswith("https://")),
        int(value.startswith("http://")),
        int(bool(re.fullmatch(
            r"\d{1,3}(?:\.\d{1,3}){3}", host
        ))),
        int(any(w in value for w in suspicious_words)),
        sum(w in value for w in suspicious_words),
        int(any(s in host for s in shorteners)),
        int(len(host.split(".")) >= 4),
        int(any(x in host for x in [
            "xn--",
            "secure-login",
            "verify-account",
            "bank-login"
        ]))
    ]


# ============================================================
# TEXT MODEL ACCURACY
# ============================================================

def check_text_accuracy():

    print("\n========================================")
    print("SMS / TEXT RANDOM FOREST MODEL")
    print("========================================")

    X = SPAM_TEXTS + HAM_TEXTS
    y = ["SPAM"] * len(SPAM_TEXTS) + ["HAM"] * len(HAM_TEXTS)

    # Split dataset into training and testing data
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # Create TF-IDF + Random Forest model
    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=1,
                sublinear_tf=True
            )
        ),
        (
            "rf",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=18,
                random_state=42,
                class_weight="balanced",
                n_jobs=-1
            )
        )
    ])

    # Train
    model.fit(X_train, y_train)

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(
        y_test, y_pred, pos_label="SPAM", zero_division=0
    )
    recall = recall_score(
        y_test, y_pred, pos_label="SPAM", zero_division=0
    )
    f1 = f1_score(
        y_test, y_pred, pos_label="SPAM", zero_division=0
    )

    print("\nTest Samples :", len(X_test))

    print("\nAccuracy  :", round(accuracy * 100, 2), "%")
    print("Precision :", round(precision * 100, 2), "%")
    print("Recall    :", round(recall * 100, 2), "%")
    print("F1-Score  :", round(f1 * 100, 2), "%")

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        y_test,
        y_pred,
        labels=["HAM", "SPAM"]
    ))

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        y_pred,
        labels=["HAM", "SPAM"],
        zero_division=0
    ))


# ============================================================
# URL MODEL ACCURACY
# ============================================================

def check_url_accuracy():

    print("\n========================================")
    print("URL RANDOM FOREST MODEL")
    print("========================================")

    X = np.array([
        url_features(url)
        for url in SPAM_URLS + HAM_URLS
    ])

    y = np.array(
        ["SPAM"] * len(SPAM_URLS) +
        ["HAM"] * len(HAM_URLS)
    )

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # Create Random Forest model
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=1,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    # Train
    model.fit(X_train, y_train)

    # Predict
    y_pred = model.predict(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(
        y_test, y_pred, pos_label="SPAM", zero_division=0
    )
    recall = recall_score(
        y_test, y_pred, pos_label="SPAM", zero_division=0
    )
    f1 = f1_score(
        y_test, y_pred, pos_label="SPAM", zero_division=0
    )

    print("\nTest Samples :", len(X_test))

    print("\nAccuracy  :", round(accuracy * 100, 2), "%")
    print("Precision :", round(precision * 100, 2), "%")
    print("Recall    :", round(recall * 100, 2), "%")
    print("F1-Score  :", round(f1 * 100, 2), "%")

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        y_test,
        y_pred,
        labels=["HAM", "SPAM"]
    ))

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        y_pred,
        labels=["HAM", "SPAM"],
        zero_division=0
    ))


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("############################################")
    print("#     SCAMGUARD MODEL ACCURACY CHECK       #")
    print("############################################")

    check_text_accuracy()
    check_url_accuracy()

    print("\n========================================")
    print("Accuracy evaluation completed.")
    print("========================================")