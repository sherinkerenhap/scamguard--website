"""Train ScamGuard Random Forest models.

Run:
    python train_model.py

Creates:
    models/scamguard_text_random_forest.pkl
    models/scamguard_url_random_forest.pkl
"""
from __future__ import annotations

import csv
import os
import re
from urllib.parse import urlparse

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Balanced starter corpus. It is intentionally bundled so the project can train
# without requiring an external dataset or internet connection.
SPAM_TEXTS = [
    "Congratulations you won a cash prize click the link now",
    "URGENT your bank account will be blocked verify immediately",
    "You have won a free iPhone claim your reward now",
    "Selected for lottery send your bank details to receive prize",
    "Your debit card will be blocked unless you update information",
    "Click here to receive your cash prize immediately",
    "Your account is suspended verify your password now",
    "Send money now to complete your registration and get the job",
    "URGENT share your OTP to confirm your bank transaction",
    "Free reward waiting for you click the link to claim",
    "Work from home job pay registration fee to start",
    "Credit card verification required send your CVV",
    "KYC update required click this link immediately",
    "Your bank account needs verification submit OTP now",
    "You are selected for a prize provide card details",
    "Refund is waiting click the payment link to receive money",
    "Your UPI account will be blocked verify now",
    "Win a lottery reward send processing fee today",
    "Dear customer confirm your PIN to avoid account suspension",
    "Urgent payment required to prevent legal action",
    "Your parcel is held pay customs fee through this link",
    "Job offer confirmed pay security deposit to receive joining letter",
    "Click immediately to activate your bank account",
    "Account security alert login and verify your identity here",
    "You have received a reward claim it before it expires",
    "Share the OTP with our agent to complete verification",
    "Your SIM will be deactivated update KYC now",
    "Electricity connection will be disconnected pay overdue bill here",
    "Tax refund available enter bank details to receive it",
    "Investment profit guaranteed send money to unlock withdrawal",
    "Your wallet is frozen click to restore access",
    "Password expired verify your account using this link",
    "Congratulations selected for a government benefit submit details",
    "Emergency verify your bank account or it will be closed",
    "Payment failed click this link and enter card information",
    "Free gift voucher claim now by paying a small fee",
    "You won a smartphone send delivery charge to claim",
    "Your courier needs address confirmation through this link",
    "Bank security team asks for OTP and PIN immediately",
    "Account verification requires your CVV and OTP",
    "Special loan approved pay processing fee now",
]

HAM_TEXTS = [
    "Your OTP is 458921. Do not share it with anyone.",
    "Meeting is scheduled for tomorrow at 10 AM.",
    "Your electricity bill is due. Please check the official portal.",
    "Your order has been shipped and will arrive tomorrow.",
    "Please find the meeting details attached.",
    "Your appointment is confirmed for Monday at 11 AM.",
    "Your bank transaction of 500 rupees was successful.",
    "Your monthly statement is available in the official banking app.",
    "Your package will be delivered today between 2 and 5 PM.",
    "The college seminar starts at 9 AM in the main auditorium.",
    "Please submit the assignment before Friday.",
    "Your exam timetable has been published on the college portal.",
    "Your library book is due next week.",
    "The meeting room has been changed to Block B.",
    "Your payment receipt is available in your account.",
    "Your salary has been credited to your account.",
    "Your electricity payment was received successfully.",
    "Your appointment reminder is scheduled for tomorrow.",
    "The order you placed has been dispatched.",
    "Please use the official website to manage your account.",
    "Your password was changed successfully.",
    "The bank branch will be closed on Sunday.",
    "Your insurance policy document is available in the portal.",
    "Your train ticket booking is confirmed.",
    "Your college fee receipt is ready to download.",
    "The team meeting is moved to Friday afternoon.",
    "Your parcel has reached the local delivery center.",
    "Please contact customer support using the official number.",
    "Your order cancellation has been processed.",
    "The appointment has been rescheduled to Monday.",
    "Your account statement can be viewed in the official app.",
    "Your subscription renewal was completed successfully.",
    "The requested document is attached to this email.",
    "Please bring your ID card to the college event.",
    "Your project review is scheduled for tomorrow.",
    "The official portal is available for bill payment.",
    "Your payment was declined. Please use the official app to retry.",
    "Your delivery address was updated successfully.",
    "Your support request has been registered.",
    "The scholarship application status is available on the portal.",
]

SPAM_URLS = [
    "http://192.168.1.20/login",
    "http://secure-login-account.example.com/verify",
    "http://bank-verify.example.net/update-account",
    "http://claim-free-reward.example.org/prize",
    "http://tinyurl.com/claim-reward",
    "http://bit.ly/bank-verification",
    "http://verify-account-login.example.com/confirm",
    "http://payment-refund.example.net/claim?account=123456",
    "http://free-prize-winner.example.org/reward",
    "http://secure-login.example.com/verify-password",
    "http://bank-login.example.net/update/kyc",
    "http://wallet-verify.example.org/login",
    "http://192.168.10.8/payment/confirm",
    "http://account-security.example.com/verify?otp=1234",
    "http://claim-reward.example.net/free-gift",
    "http://urgent-payment.example.org/confirm",
    "http://xn--secure-login-9za.example.com/verify",
    "http://delivery-fee.example.net/pay-now",
    "http://investment-profit.example.org/withdraw",
    "http://t.co/claim-prize",
]

HAM_URLS = [
    "https://www.google.com",
    "https://www.microsoft.com",
    "https://www.apple.com",
    "https://www.amazon.in",
    "https://www.flipkart.com",
    "https://www.onlinesbi.sbi",
    "https://www.hdfcbank.com",
    "https://www.icicibank.com",
    "https://www.axisbank.com",
    "https://www.irctc.co.in",
    "https://www.incometax.gov.in",
    "https://www.uidai.gov.in",
    "https://www.annauniv.edu",
    "https://www.google.com/search?q=college",
    "https://www.microsoft.com/en-in",
    "https://www.amazon.in/orders",
    "https://www.icicibank.com/personal-banking",
    "https://www.hdfcbank.com/personal/pay",
    "https://www.irctc.co.in/nget/train-search",
    "https://www.uidai.gov.in/en/my-aadhaar/about-your-aadhaar.html",
]


def url_features(url: str):
    value = (url or "").strip().lower()
    parsed = urlparse(value if re.match(r"^https?://", value) else "http://" + value)
    host = parsed.netloc.split("@")[ -1].split(":")[0]
    path = parsed.path or ""
    query = parsed.query or ""
    suspicious_words = ["login", "verify", "verification", "account", "secure", "update", "bank", "payment", "reward", "prize", "confirm", "free", "wallet", "signin", "password", "kyc"]
    shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly"]
    return [
        len(value), len(host), len(path), len(query), value.count("."),
        value.count("-"), value.count("/"), value.count("@"), value.count("%"),
        sum(ch.isdigit() for ch in value), int(value.startswith("https://")),
        int(value.startswith("http://")),
        int(bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host))),
        int(any(w in value for w in suspicious_words)),
        sum(w in value for w in suspicious_words),
        int(any(s in host for s in shorteners)), int(len(host.split(".")) >= 4),
        int(any(x in host for x in ["xn--", "secure-login", "verify-account", "bank-login"])),
    ]


def main():
    text_x = SPAM_TEXTS + HAM_TEXTS
    text_y = ["SPAM"] * len(SPAM_TEXTS) + ["HAM"] * len(HAM_TEXTS)

    text_model = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("rf", RandomForestClassifier(n_estimators=300, max_depth=18, min_samples_leaf=1, random_state=42, class_weight="balanced", n_jobs=-1)),
    ])
    text_model.fit(text_x, text_y)
    joblib.dump(text_model, os.path.join(MODEL_DIR, "scamguard_text_random_forest.pkl"))

    url_x = np.array([url_features(x) for x in SPAM_URLS + HAM_URLS], dtype=float)
    url_y = np.array(["SPAM"] * len(SPAM_URLS) + ["HAM"] * len(HAM_URLS))
    url_model = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=1, random_state=42, class_weight="balanced", n_jobs=-1)
    url_model.fit(url_x, url_y)
    joblib.dump(url_model, os.path.join(MODEL_DIR, "scamguard_url_random_forest.pkl"))

    print("ScamGuard Random Forest models trained successfully.")
    print(f"Text samples: {len(text_x)} ({len(SPAM_TEXTS)} SPAM / {len(HAM_TEXTS)} HAM)")
    print(f"URL samples: {len(url_x)} ({len(SPAM_URLS)} SPAM / {len(HAM_URLS)} HAM)")
    print("Created:")
    print(" - models/scamguard_text_random_forest.pkl")
    print(" - models/scamguard_url_random_forest.pkl")


if __name__ == "__main__":
    main()
