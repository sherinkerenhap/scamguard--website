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
- Classification Report
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

# ============================================================
# IMPORT TRAINING DATA
# ============================================================

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
        value
        if re.match(r"^https?://", value)
        else "http://" + value
    )

    host = parsed.netloc.split("@")[-1].split(":")[0]
    path = parsed.path or ""
    query = parsed.query or ""

    suspicious_words = [
        "login",
        "verify",
        "verification",
        "account",
        "secure",
        "update",
        "bank",
        "payment",
        "reward",
        "prize",
        "confirm",
        "free",
        "wallet",
        "signin",
        "password",
        "kyc"
    ]

    shorteners = [
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "is.gd",
        "ow.ly"
    ]

    return [

        # URL length
        len(value),

        # Domain length
        len(host),

        # Path length
        len(path),

        # Query length
        len(query),

        # Number of dots
        value.count("."),

        # Number of hyphens
        value.count("-"),

        # Number of slashes
        value.count("/"),

        # Number of @ symbols
        value.count("@"),

        # Number of % symbols
        value.count("%"),

        # Number of digits
        sum(ch.isdigit() for ch in value),

        # HTTPS
        int(value.startswith("https://")),

        # HTTP
        int(value.startswith("http://")),

        # IP address
        int(
            bool(
                re.fullmatch(
                    r"\d{1,3}(?:\.\d{1,3}){3}",
                    host
                )
            )
        ),

        # Contains suspicious keyword
        int(
            any(
                word in value
                for word in suspicious_words
            )
        ),

        # Number of suspicious keywords
        sum(
            word in value
            for word in suspicious_words
        ),

        # URL shortener
        int(
            any(
                shortener in host
                for shortener in shorteners
            )
        ),

        # Too many subdomains
        int(
            len(host.split(".")) >= 4
        ),

        # Suspicious domain pattern
        int(
            any(
                pattern in host
                for pattern in [
                    "xn--",
                    "secure-login",
                    "verify-account",
                    "bank-login"
                ]
            )
        )
    ]


# ============================================================
# TEXT MODEL ACCURACY
# ============================================================

def check_text_accuracy():

    print("\n========================================")
    print("SMS / TEXT RANDOM FOREST MODEL")
    print("========================================")

    # Combine SPAM and HAM messages
    X = SPAM_TEXTS + HAM_TEXTS

    # Create labels
    y = (
        ["SPAM"] * len(SPAM_TEXTS)
        + ["HAM"] * len(HAM_TEXTS)
    )

    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42,

        stratify=y
    )

    # --------------------------------------------------------
    # TF-IDF + RANDOM FOREST MODEL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    y_pred = model.predict(
        X_test
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        pos_label="SPAM",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        pos_label="SPAM",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        pos_label="SPAM",
        zero_division=0
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print("\nTest Samples :", len(X_test))

    print(
        "Accuracy     :",
        round(accuracy * 100, 2),
        "%"
    )

    print(
        "Precision    :",
        round(precision * 100, 2),
        "%"
    )

    print(
        "Recall       :",
        round(recall * 100, 2),
        "%"
    )

    print(
        "F1-Score     :",
        round(f1 * 100, 2),
        "%"
    )

    # --------------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------------

    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            y_pred,
            labels=["HAM", "SPAM"]
        )
    )

    # --------------------------------------------------------
    # CLASSIFICATION REPORT
    # --------------------------------------------------------

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            y_pred,
            labels=["HAM", "SPAM"],
            zero_division=0
        )
    )


# ============================================================
# URL MODEL ACCURACY
# ============================================================

def check_url_accuracy():

    print("\n========================================")
    print("URL RANDOM FOREST MODEL")
    print("========================================")

    # --------------------------------------------------------
    # CREATE URL FEATURES
    # --------------------------------------------------------

    X = np.array([

        url_features(url)

        for url in SPAM_URLS + HAM_URLS
    ])

    # --------------------------------------------------------
    # CREATE LABELS
    # --------------------------------------------------------

    y = np.array(

        ["SPAM"] * len(SPAM_URLS)

        + ["HAM"] * len(HAM_URLS)
    )

    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    #
    # 30% is used for testing instead of 20%.
    # This gives a larger evaluation set.
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.30,

        random_state=42,

        stratify=y
    )

    # --------------------------------------------------------
    # RANDOM FOREST MODEL
    # --------------------------------------------------------

    model = RandomForestClassifier(

        n_estimators=300,

        max_depth=12,

        min_samples_leaf=1,

        random_state=42,

        class_weight="balanced",

        n_jobs=-1
    )

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model.fit(

        X_train,
        y_train
    )

    # --------------------------------------------------------
    # PREDICT
    # --------------------------------------------------------

    y_pred = model.predict(

        X_test
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    accuracy = accuracy_score(

        y_test,
        y_pred
    )

    precision = precision_score(

        y_test,
        y_pred,

        pos_label="SPAM",

        zero_division=0
    )

    recall = recall_score(

        y_test,
        y_pred,

        pos_label="SPAM",

        zero_division=0
    )

    f1 = f1_score(

        y_test,
        y_pred,

        pos_label="SPAM",

        zero_division=0
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print("\nTest Samples :", len(X_test))

    print(
        "Accuracy     :",
        round(accuracy * 100, 2),
        "%"
    )

    print(
        "Precision    :",
        round(precision * 100, 2),
        "%"
    )

    print(
        "Recall       :",
        round(recall * 100, 2),
        "%"
    )

    print(
        "F1-Score     :",
        round(f1 * 100, 2),
        "%"
    )

    # --------------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------------

    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            y_pred,
            labels=["HAM", "SPAM"]
        )
    )

    # --------------------------------------------------------
    # CLASSIFICATION REPORT
    # --------------------------------------------------------

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            y_pred,
            labels=["HAM", "SPAM"],
            zero_division=0
        )
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("\n")

    print("############################################")
    print("#       SCAMGUARD MODEL ACCURACY CHECK     #")
    print("############################################")

    # Check SMS/Text model
    check_text_accuracy()

    # Check URL model
    check_url_accuracy()

    print("\n========================================")
    print("Accuracy evaluation completed.")
    print("========================================")