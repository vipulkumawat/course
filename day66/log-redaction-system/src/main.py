from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
import re

app = FastAPI(title="Log Redaction System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Log Redaction System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "log-redaction-api"}

def redact_log(log: str) -> str:
    # Redact emails
    log = re.sub(r"[\w\.-]+@[\w\.-]+", "[REDACTED_EMAIL]", log)
    # Redact credit card numbers (simple pattern)
    log = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CREDIT_CARD]", log)
    return log

@app.get("/logs/demo", response_model=List[str])
async def get_demo_logs():
    demo_logs = [
        "User john.doe@example.com logged in.",
        "Payment processed for card 4111 1111 1111 1111.",
        "No sensitive info here.",
        "Contact admin@company.com for support.",
        "Card 5500-0000-0000-0004 used by jane@doe.com."
    ]
    return [redact_log(log) for log in demo_logs]

@app.get("/logs/demo/original", response_model=List[str])
async def get_original_logs():
    return [
        "User john.doe@example.com logged in.",
        "Payment processed for card 4111 1111 1111 1111.",
        "No sensitive info here.",
        "Contact admin@company.com for support.",
        "Card 5500-0000-0000-0004 used by jane@doe.com."
    ]

@app.get("/logs/demo/redacted", response_model=List[str])
async def get_redacted_logs():
    original_logs = [
        "User john.doe@example.com logged in.",
        "Payment processed for card 4111 1111 1111 1111.",
        "No sensitive info here.",
        "Contact admin@company.com for support.",
        "Card 5500-0000-0000-0004 used by jane@doe.com."
    ]
    return [redact_log(log) for log in original_logs]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
