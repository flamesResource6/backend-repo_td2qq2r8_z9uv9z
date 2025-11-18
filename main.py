import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal

from database import create_document, get_documents
from schemas import Inquiry, NewsletterSubscriber

app = FastAPI(title="Xyber Clan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Xyber Clan API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from Xyber Clan backend API!"}


# Brand info (for frontend display)
@app.get("/api/brand")
def brand_info():
    return {
        "name": "Xyber Clan",
        "tagline": "Web Services • Security Audits • Design",
        "description": "We craft fast web experiences, harden your security, and design bold digital brands.",
    }


# Public services listing
class Service(BaseModel):
    key: Literal["web", "security", "design"]
    title: str
    description: str
    features: List[str]


@app.get("/api/services", response_model=List[Service])
def list_services():
    return [
        Service(
            key="web",
            title="Web Services",
            description="Full-stack web apps, landing pages, and API development.",
            features=[
                "Modern React frontends",
                "Fast APIs with Python/FastAPI",
                "Deployments & CI/CD",
            ],
        ),
        Service(
            key="security",
            title="Security Audit",
            description="Offensive security assessments and hardening recommendations.",
            features=[
                "Black/gray-box testing",
                "OWASP Top 10 coverage",
                "Actionable remediation report",
            ],
        ),
        Service(
            key="design",
            title="Design",
            description="Branding, UI/UX, and design systems with a cyber edge.",
            features=[
                "Brand identity & guidelines",
                "UI kits & components",
                "Prototyping & usability",
            ],
        ),
    ]


# Inquiries (lead capture)
@app.post("/api/inquiries")
def create_inquiry(inquiry: Inquiry):
    try:
        inquiry_id = create_document("inquiry", inquiry)
        return {"success": True, "id": inquiry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Newsletter subscribe (simple de-duplication)
@app.post("/api/subscribe")
def subscribe(payload: NewsletterSubscriber):
    try:
        existing = get_documents("newslettersubscriber", {"email": payload.email}, limit=1)
        if existing:
            return {"success": True, "message": "Already subscribed"}
        sub_id = create_document("newslettersubscriber", payload)
        return {"success": True, "id": sub_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
