
# =========================================================
# ScamGuard - Flask Application
# Render + Aiven MySQL
# =========================================================

import os
import re
from datetime import datetime
from difflib import SequenceMatcher

from flask import Flask, jsonify, render_template, request
import mysql.connector

from ml_detector import predict_text, predict_url

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")


# =========================================================
# MYSQL CONFIGURATION
# =========================================================

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "scamguard")


def get_mysql_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        ssl_disabled=False,
        connection_timeout=15
    )


# =========================================================
# DATABASE CONNECTION TEST
# =========================================================

def test_database_connection():
    db = None
    cursor = None
    try:
        db = get_mysql_connection()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    except Exception as error:
        print("MySQL connection error:", error)
        return False
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# =========================================================
# DATABASE TABLE SETUP
# =========================================================

def setup_database():
    db = None
    cursor = None

    try:
        db = get_mysql_connection()
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scam_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message TEXT NOT NULL,
                label VARCHAR(20) NOT NULL,
                source VARCHAR(100) DEFAULT 'ScamGuard',
                category VARCHAR(100) DEFAULT 'SMS',
                risk_score INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message TEXT NOT NULL,
                result VARCHAR(100) NOT NULL,
                risk_score INT DEFAULT 0,
                risk_level VARCHAR(30) DEFAULT 'LOW',
                detected_indicators TEXT,
                recommendation TEXT,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.commit()
        print("Database tables are ready.")
        return True

    except Exception as error:
        print("Database setup failed:", error)
        return False

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# =========================================================
# SAVE SCAN HISTORY
# =========================================================

def save_scan_history(content, result):
    db = None
    cursor = None

    indicators = ", ".join(result.get("matched_words", []))
    if not indicators:
        indicators = ", ".join(result.get("reasons", []))

    try:
        db = get_mysql_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO scan_history (
                message, result, risk_score, risk_level,
                detected_indicators, recommendation
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            content,
            result.get("result", "UNKNOWN"),
            int(result.get("risk_score", 0)),
            result.get("risk_level", "LOW"),
            indicators,
            result.get("recommendation", "")
        ))

        db.commit()
        print("Scan saved successfully.")
        return True

    except Exception as error:
        print("MySQL save failed:", error)
        return False

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# =========================================================
# GET SCAN HISTORY
# =========================================================

def get_history(limit=50):
    db = None
    cursor = None

    try:
        db = get_mysql_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, message, result, risk_score, risk_level,
                   detected_indicators, recommendation, scanned_at
            FROM scan_history
            ORDER BY id DESC
            LIMIT %s
        """, (int(limit),))

        return cursor.fetchall()

    except Exception as error:
        print("History read failed:", error)
        return []

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# =========================================================
# TEXT NORMALIZATION AND SIMILARITY
# =========================================================

def normalize_text(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def calculate_similarity(text1, text2):
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0

    return SequenceMatcher(None, text1, text2).ratio()


# =========================================================
# FIND DATABASE MATCH
# =========================================================

def find_database_match(message):
    db = None
    cursor = None

    try:
        db = get_mysql_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, message, label, source, category, risk_score
            FROM scam_messages
        """)

        rows = cursor.fetchall()
        if not rows:
            return None

        best_spam = None
        best_ham = None

        for row in rows:
            similarity = calculate_similarity(message, row["message"])
            row["similarity"] = similarity
            label = str(row.get("label", "")).upper()

            if label == "SPAM":
                if best_spam is None or similarity > best_spam["similarity"]:
                    best_spam = row

            elif label == "HAM":
                if best_ham is None or similarity > best_ham["similarity"]:
                    best_ham = row

        if best_spam and best_ham:
            if best_spam["similarity"] >= best_ham["similarity"]:
                return best_spam
            return best_ham

        return best_spam or best_ham

    except Exception as error:
        print("Database matching error:", error)
        return None

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# =========================================================
# GLOBAL TEMPLATE VARIABLES
# =========================================================

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}


# =========================================================
# WEBSITE ROUTES
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/sms-detection")
def sms_detection():
    return render_template("sms_detection.html")


@app.route("/url-analysis")
def url_analysis():
    return render_template("url_analysis.html")


@app.route("/url-scan")
def url_scan():
    return render_template("url_scan.html")


@app.route("/explainable-results")
def explainable_results():
    return render_template("explainable_results.html")


@app.route("/risk-classification")
def risk_classification():
    return render_template("risk_classification.html")


@app.route("/safety-recommendations")
def safety_recommendations():
    return render_template("safety_recommendations.html")


@app.route("/scan")
def scan():
    scan_type = request.args.get("type", "message").lower()

    if scan_type not in ("message", "url"):
        scan_type = "message"

    return render_template("scan.html", scan_type=scan_type)


@app.route("/how")
def how():
    return render_template("how.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/email")
def email():
    return render_template("email.html")


@app.route("/sms")
def sms():
    return render_template("sms.html")


@app.route("/history")
def history():
    return render_template("history.html", scans=get_history())


# =========================================================
# SCAM DETECTION RULES
# =========================================================

SCAM_RULES = {
    "Urgent language": [
        "urgent", "immediately", "act now", "last chance",
        "within 24 hours", "verify now", "do it now"
    ],
    "OTP request": [
        "otp", "one time password", "verification code"
    ],
    "Bank/card information": [
        "bank account", "account number", "card number", "cvv",
        "debit card", "credit card", "bank details"
    ],
    "Password request": [
        "password", "login password", "pin", "mpin"
    ],
    "Payment request": [
        "send money", "transfer money", "pay now",
        "payment required", "make payment", "registration fee"
    ],
    "Prize/reward claim": [
        "you won", "winner", "prize", "reward", "lottery",
        "cash prize", "congratulations"
    ],
    "Fake job indicators": [
        "work from home", "job offer", "selected for job",
        "earn money", "part time job", "registration fee"
    ],
    "Account threat": [
        "account will be blocked", "account blocked",
        "account suspended", "verify your account"
    ],
    "Suspicious link request": [
        "click here", "click immediately",
        "click the link", "open this link"
    ]
}


# =========================================================
# MESSAGE ANALYSIS
# =========================================================

def analyze_text(text):
    text = (text or "").strip()
    lower = text.lower()
    reasons = []
    matched_words = []

    try:
        ml_result = predict_text(text) or {}
    except Exception as error:
        print("Text ML prediction failed:", error)
        ml_result = {}

    ml_score = int(ml_result.get("score", 0) or 0)
    ml_label = ml_result.get("label", "UNKNOWN")

    if ml_result.get("available"):
        reasons.append(
            f"Random Forest classified the message as {ml_label} "
            f"({ml_score}% scam probability)"
        )

    for rule_name, keywords in SCAM_RULES.items():
        found = [word for word in keywords if word in lower]
        if found:
            reasons.append(rule_name)
            matched_words.extend(found)

    urls = re.findall(r"https?://[^\s]+|www\.[^\s]+", lower)
    if urls:
        reasons.append("Contains a URL")

    rule_score = min(len(reasons) * 10 + len(matched_words) * 2, 100)

    database_match = find_database_match(text)
    database_score = 0
    database_similarity = 0
    database_label = None
    database_message = None

    if database_match:
        database_similarity = database_match["similarity"]
        database_label = str(database_match.get("label", "")).upper()
        database_score = int(database_match.get("risk_score") or 0)
        database_message = database_match.get("message")

        if database_similarity >= 0.80:
            reasons.append("Highly similar message found in the database")
        elif database_similarity >= 0.60 and database_label == "SPAM":
            reasons.append("Similar suspicious message found in the database")

    if ml_result.get("available"):
        final_score = int(round(
            ml_score * 0.70 + rule_score * 0.20 + database_score * 0.10
        ))
    else:
        final_score = rule_score
        if database_match and database_label == "SPAM":
            final_score = max(final_score, database_score)

    if database_match and database_label == "SPAM" and database_similarity >= 0.80:
        final_score = max(final_score, min(database_score, 100))

    final_score = min(max(int(final_score), 0), 100)

    if final_score <= 25:
        level, result = "LOW", "SAFE"
        recommendation = (
            "No major scam indicators were detected. Still verify unexpected "
            "messages before sharing personal information."
        )
    elif final_score <= 50:
        level, result = "MEDIUM", "SUSPICIOUS"
        recommendation = (
            "Some suspicious indicators were detected. Verify the sender before "
            "clicking links, making payments, or sharing personal information."
        )
    elif final_score <= 75:
        level, result = "HIGH", "HIGH RISK"
        recommendation = (
            "Strong scam indicators are present. Avoid clicking links, sharing "
            "sensitive information, or making payments."
        )
    else:
        level, result = "CRITICAL", "LIKELY SCAM"
        recommendation = (
            "Multiple serious scam indicators are present. Stop interaction "
            "immediately and verify the source through an official channel."
        )

    if not reasons:
        reasons = ["No major scam indicators detected"]

    try:
        ml_probability = round(
            float(ml_result.get("probability", 0) or 0) * 100, 2
        )
    except (TypeError, ValueError):
        ml_probability = 0

    return {
        "result": result,
        "risk_score": final_score,
        "risk_level": level,
        "reasons": reasons,
        "matched_words": matched_words,
        "recommendation": recommendation,
        "database_similarity": round(database_similarity, 3),
        "database_label": database_label,
        "database_message": database_message,
        "ml_algorithm": "Random Forest",
        "ml_prediction": ml_label,
        "ml_probability": ml_probability,
        "ml_model_available": bool(ml_result.get("available"))
    }


# =========================================================
# URL ANALYSIS
# =========================================================

def analyze_url(url):
    url = (url or "").strip()
    lower = url.lower()
    reasons = []
    matched = []

    if not url:
        return {
            "result": "INVALID",
            "risk_score": 0,
            "risk_level": "LOW",
            "reasons": ["URL is empty"],
            "matched_words": [],
            "recommendation": "Please enter a valid URL.",
            "ml_algorithm": "Random Forest",
            "ml_prediction": "UNKNOWN",
            "ml_probability": 0,
            "ml_model_available": False
        }

    try:
        ml_result = predict_url(url) or {}
    except Exception as error:
        print("URL ML prediction failed:", error)
        ml_result = {}

    ml_score = int(ml_result.get("score", 0) or 0)
    ml_label = ml_result.get("label", "UNKNOWN")

    if ml_result.get("available"):
        reasons.append(
            f"Random Forest classified the URL as {ml_label} "
            f"({ml_score}% scam probability)"
        )

    if not re.match(r"^https?://", lower):
        reasons.append("URL does not start with HTTP/HTTPS")

    if lower.startswith("http://"):
        reasons.append("Website is not using HTTPS")

    suspicious_words = [
        "login", "verify", "verification", "account", "secure",
        "update", "bank", "payment", "reward", "prize", "confirm",
        "free", "wallet", "signin", "password", "kyc"
    ]

    matched = [word for word in suspicious_words if word in lower]
    if matched:
        reasons.append("Suspicious keywords found in URL")

    if re.search(r"https?://\d{1,3}(?:\.\d{1,3}){3}", lower):
        reasons.append("URL uses an IP address")

    if len(url) > 75:
        reasons.append("Unusually long URL")

    if lower.count(".") >= 4:
        reasons.append("Multiple subdomains detected")

    shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly"]
    if any(short in lower for short in shorteners):
        reasons.append("URL shortening service detected")

    if "@" in url:
        reasons.append("URL contains an @ symbol")

    if lower.count("-") >= 4:
        reasons.append("URL contains many hyphens")

    rule_score = min(len(reasons) * 10 + len(matched) * 4, 100)

    if ml_result.get("available"):
        score = int(round(ml_score * 0.75 + rule_score * 0.25))
    else:
        score = rule_score

    score = min(max(score, 0), 100)

    if score <= 25:
        level, result = "LOW", "SAFE"
        recommendation = (
            "No major URL indicators were detected. Verify the domain before "
            "entering sensitive information."
        )
    elif score <= 50:
        level, result = "MEDIUM", "SUSPICIOUS"
        recommendation = (
            "Check the domain carefully and avoid entering personal or financial "
            "information until verified."
        )
    elif score <= 75:
        level, result = "HIGH", "HIGH RISK"
        recommendation = (
            "Avoid interacting with this URL until its authenticity is "
            "independently verified."
        )
    else:
        level, result = "CRITICAL", "LIKELY SCAM"
        recommendation = (
            "Avoid opening the URL and do not provide passwords, OTPs, payment "
            "details, or personal information."
        )

    if not reasons:
        reasons = ["No major URL indicators detected"]

    try:
        ml_probability = round(
            float(ml_result.get("probability", 0) or 0) * 100, 2
        )
    except (TypeError, ValueError):
        ml_probability = 0

    return {
        "result": result,
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons,
        "matched_words": matched,
        "recommendation": recommendation,
        "ml_algorithm": "Random Forest",
        "ml_prediction": ml_label,
        "ml_probability": ml_probability,
        "ml_model_available": bool(ml_result.get("available"))
    }

# =========================================================
# MESSAGE SCAN API
# =========================================================

@app.route("/api/check-text", methods=["POST"])
def api_check_text():
    data = request.get_json(silent=True) or {}
    text_value = (data.get("text") or "").strip()

    if not text_value:
        return jsonify({
            "success": False,
            "error": "Please enter a message."
        }), 400

    try:
        result = analyze_text(text_value)
        saved = save_scan_history(text_value, result)

        if not saved:
            return jsonify({
                "success": False,
                "error": (
                    "The message was analyzed, but it could not be saved "
                    "to the MySQL database. Check Render logs."
                )
            }), 500

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as error:
        print("MESSAGE API ERROR:", error)
        return jsonify({
            "success": False,
            "error": "Message analysis failed. Check Render logs."
        }), 500


# =========================================================
# URL SCAN API
# =========================================================

@app.route("/api/check-url", methods=["POST"])
def api_check_url():
    data = request.get_json(silent=True) or {}
    url_value = (data.get("url") or "").strip()

    if not url_value:
        return jsonify({
            "success": False,
            "error": "Please enter a URL."
        }), 400

    try:
        result = analyze_url(url_value)
        saved = save_scan_history(url_value, result)

        if not saved:
            return jsonify({
                "success": False,
                "error": (
                    "The URL was analyzed, but it could not be saved "
                    "to the MySQL database. Check Render logs."
                )
            }), 500

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as error:
        print("URL API ERROR:", error)
        return jsonify({
            "success": False,
            "error": "URL analysis failed. Check Render logs."
        }), 500


# =========================================================
# DATABASE STATUS
# =========================================================

@app.route("/db-status")
def db_status():
    db = None
    cursor = None

    try:
        db = get_mysql_connection()
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM scam_messages")
        message_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scan_history")
        scan_count = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "database": "Aiven MySQL",
            "scam_messages": message_count,
            "scan_history": scan_count
        })

    except Exception as error:
        print("Database status error:", error)
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# =========================================================
# CREATE TABLES WHEN RENDER/GUNICORN STARTS
# =========================================================

if test_database_connection():
    print("Aiven MySQL connected successfully.")
    setup_database()
else:
    print(
        "Aiven MySQL connection failed. "
        "Check DB_HOST, DB_PORT, DB_NAME, DB_USER and DB_PASSWORD."
    )


# =========================================================
# LOCAL DEVELOPMENT
# Render uses: gunicorn app:app
# =========================================================

if __name__ == "__main__":
    print("ScamGuard starting...")

    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000"))
    )
