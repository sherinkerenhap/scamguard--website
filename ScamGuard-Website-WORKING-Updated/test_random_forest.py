"""Quick offline test for the bundled Random Forest models."""
from ml_detector import predict_text, predict_url

cases = [
    ("TEXT", "URGENT! Your bank account will be blocked. Verify immediately."),
    ("TEXT", "Meeting is scheduled for tomorrow at 10 AM."),
    ("URL", "http://secure-login-account.example.com/verify"),
    ("URL", "https://www.google.com"),
]

for kind, value in cases:
    result = predict_text(value) if kind == "TEXT" else predict_url(value)
    print(f"{kind}: {value}")
    print(f"  Algorithm : {result.get('algorithm')}")
    print(f"  Prediction: {result.get('label')}")
    print(f"  Probability: {result.get('score')}%")
    print()
