import re

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator
from url_checks import analyze_urls
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="PhishGuard API",
    description="Analyzes suspicious messages and URLs for phishing indicators.",
    version="0.1.0",
)


class AnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Enter a message to analyze.")
        return value.strip()


# Each rule contributes points once, regardless of repeated matches.
RULES = [
    {
        "id": "urgency",
        "pattern": r"\b(urgent|immediately|act now|within 24 hours)\b",
        "points": 15,
        "explanation": "Urgent language can pressure you to act without checking.",
    },
    {
        "id": "account_threat",
        "pattern": (
            r"\b(account suspended|account will be suspended|"
            r"account locked|account will be closed)\b"
        ),
        "points": 20,
        "explanation": "Account threats can push you into following unsafe instructions.",
    },
    {
        "id": "credential_request",
        "pattern": (
            r"\b(verify your password|confirm your password|"
            r"send your password|enter your password|"
            r"share your verification code|send your otp)\b"
        ),
        "points": 30,
        "explanation": "Requests for passwords or verification codes need careful scrutiny.",
    },
    {
        "id": "payment_request",
        "pattern": r"\b(gift cards?|wire transfer|send money|pay immediately)\b",
        "points": 20,
        "explanation": "These payment requests can appear in financial scams.",
    },
    {
        "id": "prize_claim",
        "pattern": r"\b(you have won|you won|claim your prize|claim your reward)\b",
        "points": 15,
        "explanation": "Unexpected prizes can be used to lure you into a scam.",
    },
]

@app.get("/api/health")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "PhishGuard API"}

@app.post("/api/analyze")
@app.post("/analyze")
def analyze_message(request: AnalysisRequest):
    findings = []
    score = 0

    for rule in RULES:
        match = re.search(rule["pattern"], request.text, flags=re.IGNORECASE)
        if match:
            score += rule["points"]
            findings.append({
                "id": rule["id"],
                "matched_text": match.group(0),
                "points": rule["points"],
                "explanation": rule["explanation"],
            })

    url_findings = analyze_urls(request.text)
    findings.extend(url_findings)
    score += sum(finding["points"] for finding in url_findings)
    score = min(score, 100)

    if score >= 60:
        risk_level = "High"
    elif score >= 25:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "score": score,
        "risk_level": risk_level,
        "findings": findings,
        "notice": (
            "This is a rule-based warning score, not a probability of phishing. "
            "A low score does not guarantee safety. Context and negation "
            "can affect results. Links are inspected as text only; "
            "destinations are not visited or checked against threat databases."
        ),
    }
   
FRONTEND_DIST = (
    Path(__file__).resolve().parent.parent / "frontend" / "dist"
)

if FRONTEND_DIST.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="frontend",
    )