"""Groq AI client — uses Groq API with LLaMA3-70b for all agent prompts."""
import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"


def _get_headers() -> dict:
    """Build Groq auth headers."""
    return {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY', '')}",
        "Content-Type": "application/json",
    }


def call_groq(system_prompt: str, user_prompt: str) -> str:
    """Send system + user prompt to Groq and return the text response."""
    payload = {
        "model": os.getenv("GROQ_MODEL", GROQ_MODEL),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    response = httpx.post(
        os.getenv("GROQ_API_URL", GROQ_API_URL),
        headers=_get_headers(),
        json=payload,
        timeout=120,
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    raise Exception(f"Groq API error: {response.status_code} {response.text}")


async def run_agent_prompt(system_prompt: str, user_prompt: str) -> str:
    """
    High-level async helper: calls Groq LLaMA3-70b with system + user prompts.
    Falls back to structured mock if API key is not configured.
    """
    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key:
        logger.warning("Groq API key not configured — returning mock response")
        return _mock_response(system_prompt + " " + user_prompt)

    try:
        result = call_groq(system_prompt, user_prompt)
        logger.info("Groq API call successful")
        return result
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return _mock_response(system_prompt + " " + user_prompt)


def _mock_response(prompt: str) -> str:
    """
    Generate structured JSON mock responses.
    Uses ONLY first 200 chars (system_prompt) for agent type detection
    to avoid false matches from context data in user prompts.
    """
    p_head = prompt[:200].lower()  # system prompt only
    p = prompt.lower()             # full prompt for idea extraction

    # Extract idea text from prompt
    idea_snippet = "AI-powered startup solution"
    for marker in ["startup idea:", "idea:", "idea\n"]:
        if marker in p:
            idx = p.index(marker)
            raw = prompt[idx + len(marker):idx + len(marker) + 120].strip()
            idea_snippet = raw.split("\n")[0].strip()[:100]
            break

    # --- Agent detection via system_prompt signatures ---
    if "validator" in p_head:
        return _validator_mock(idea_snippet)
    elif "strategy expert" in p_head or "go-to-market" in p_head:
        return _strategy_mock(idea_snippet)
    elif "software architect" in p_head:
        return _architect_mock(idea_snippet)
    elif "full-stack developer" in p_head:
        return _code_mock(idea_snippet)
    elif "cybersecurity" in p_head or "owasp" in p_head:
        return _security_mock()
    elif "copywriter" in p_head or "pitch deck creator" in p_head:
        return _copy_mock(idea_snippet)
    elif "seo expert" in p_head:
        return _seo_mock(idea_snippet)
    return _validator_mock(idea_snippet)  # fallback


def _validator_mock(idea: str) -> str:
    import json
    return json.dumps({
        "refinedIdea": f"{idea}",
        "problemStatement": "Current solutions are slow, expensive, or inaccessible for target users.",
        "targetAudience": "Early adopters aged 25–40, tech-savvy, motivated to solve this problem.",
        "proposedSolution": f"An AI-powered platform delivering {idea} with automated workflows.",
        "marketOpportunity": "Large and growing market with limited high-quality alternatives.",
        "marketScore": 78,
        "tam": "$12B", "sam": "$2.4B", "som": "$240M",
        "competitors": ["Legacy Incumbent (slow, expensive)", "Point Solution A (limited)", "Manual Process (no software)"],
        "riskFlags": ["Competitive pressure from incumbents", "User adoption curve", "Regulatory requirements"],
        "recommendation": "PROCEED — Strong problem-solution fit with clear market opportunity and defensible differentiation."
    }, indent=2)


def _strategy_mock(idea: str) -> str:
    import json
    return json.dumps({
        "monetizationModel": "Freemium SaaS with subscription upgrade",
        "pricingTiers": {"free": "$0 — core features, 3 uses/month", "pro": "$49/mo — unlimited", "team": "$199/mo — 10 seats"},
        "gtmStrategy": "Product-led growth via freemium, viral referrals, and SEO content marketing.",
        "targetChannels": ["Product Hunt", "Twitter/X founder community", "IndieHackers", "LinkedIn", "SEO/blog"],
        "launchTimeline": {"week1": "Soft launch + Product Hunt", "month1": "100 beta users + community", "month3": "50 paying customers"},
        "competitivePositioning": "Faster, cheaper, and more complete than alternatives.",
        "revenueProjection": {"month6": "$50K ARR", "year1": "$300K ARR"}
    }, indent=2)


def _architect_mock(idea: str) -> str:
    import json
    return json.dumps({
        "recommendedStack": {"frontend": "Next.js 14 (App Router)", "backend": "FastAPI (Python)", "database": "PostgreSQL", "cache": "Redis", "hosting": "Vercel + Railway"},
        "systemDesign": "Three-tier: Next.js SPA → FastAPI REST → PostgreSQL. Redis for caching and sessions. Async task queue for background jobs.",
        "coreFeatures": ["User authentication (JWT)", "Core CRUD module", "Real-time updates (SSE/WS)", "File uploads (S3)", "Analytics dashboard"],
        "dataModel": {"tables": ["users: id, email, password_hash, tier, created_at", "items: id, user_id, title, content, status, created_at", "events: id, user_id, type, payload, timestamp"]},
        "apiEndpoints": [
            {"method": "POST", "path": "/api/auth/register", "description": "User registration"},
            {"method": "POST", "path": "/api/auth/login", "description": "Login + JWT token"},
            {"method": "GET", "path": "/api/items", "description": "List user items"},
            {"method": "POST", "path": "/api/items", "description": "Create item"},
            {"method": "GET", "path": "/api/analytics", "description": "Usage stats"}
        ],
        "scalabilityNotes": "Stateless API + Redis sessions enables horizontal scaling. CDN for assets."
    }, indent=2)


def _code_mock(idea: str) -> str:
    import json
    return json.dumps({
        "projectName": "startup-mvp",
        "techStack": "Next.js 14 + FastAPI + PostgreSQL + Tailwind CSS",
        "readmeSummary": f"MVP codebase for: {idea}. Full-stack with auth, core features, and REST API.",
        "files": [
            {"path": "frontend/app/page.tsx", "description": "Landing page with hero and CTA",
             "content": "'use client'\nexport default function Home() {\n  return (\n    <main className=\"min-h-screen bg-gray-900 text-white p-8\">\n      <h1 className=\"text-5xl font-bold mb-4\">Welcome to Your Startup</h1>\n      <p className=\"text-gray-400\">The fastest way to solve your problem.</p>\n      <button className=\"mt-6 px-6 py-3 bg-purple-600 rounded-xl font-semibold\">Get Started Free</button>\n    </main>\n  )\n}"},
            {"path": "frontend/app/dashboard/page.tsx", "description": "User dashboard",
             "content": "'use client'\nimport { useEffect, useState } from 'react'\nexport default function Dashboard() {\n  const [items, setItems] = useState([])\n  useEffect(() => { fetch('/api/items').then(r=>r.json()).then(setItems) }, [])\n  return (\n    <div className=\"p-8\">\n      <h2 className=\"text-2xl font-bold mb-4\">Dashboard</h2>\n      <ul>{items.map((item: any) => <li key={item.id} className=\"p-2 border-b\">{item.title}</li>)}</ul>\n    </div>\n  )\n}"},
            {"path": "backend/main.py", "description": "FastAPI entry point with auth and CRUD",
             "content": "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI(title='Startup MVP API', version='1.0.0')\napp.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])\n\n@app.get('/api/health')\ndef health(): return {'status': 'ok', 'version': '1.0.0'}\n\n@app.post('/api/auth/register')\ndef register(email: str, password: str):\n    return {'message': 'User created', 'token': 'jwt-token'}\n\n@app.get('/api/items')\ndef list_items(): return [{'id': 1, 'title': 'Sample Item', 'status': 'active'}]"},
            {"path": "backend/models.py", "description": "SQLAlchemy data models",
             "content": "from sqlalchemy import Column, String, DateTime\nfrom sqlalchemy.ext.declarative import declarative_base\nimport uuid; Base = declarative_base()\n\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))\n    email = Column(String(255), unique=True, nullable=False)\n    tier = Column(String(20), default='free')"},
            {"path": "README.md", "description": "Setup and run instructions",
             "content": f"# Startup MVP\n\n## Quick Start\n```bash\n# Frontend\ncd frontend && npm install && npm run dev\n\n# Backend\ncd backend && pip install fastapi uvicorn sqlalchemy && uvicorn main:app --reload\n```\n\n## Deploy\n- Frontend: Vercel (connect GitHub repo)\n- Backend: Railway or Render\n"}
        ],
        "setupInstructions": [
            "Clone repo: git clone <your-repo>",
            "Frontend: cd frontend && npm install && npm run dev (port 3000)",
            "Backend: cd backend && pip install -r requirements.txt && uvicorn main:app --reload (port 8000)",
            "Database: Set DATABASE_URL in .env",
            "Open http://localhost:3000"
        ],
        "envVariables": ["DATABASE_URL=postgresql://localhost/startup_mvp", "JWT_SECRET=your-secret-key-32-chars", "NEXT_PUBLIC_API_URL=http://localhost:8000"],
        "testSuite": "Backend: pytest (unit + integration). Frontend: Playwright E2E tests."
    }, indent=2)


def _security_mock() -> str:
    import json
    return json.dumps({
        "overallScore": 74,
        "badge": "SECURITY_REVIEWED",
        "owaspAudit": [
            {"id": "A01", "name": "Broken Access Control", "status": "WARN", "severity": "Medium", "description": "Some endpoints lack authorization checks.", "fix": "Add JWT middleware to all protected routes."},
            {"id": "A02", "name": "Cryptographic Failures", "status": "WARN", "severity": "Medium", "description": "Password hashing needs stronger algorithm.", "fix": "Use bcrypt with cost factor ≥12."},
            {"id": "A03", "name": "Injection", "status": "PASS", "severity": "N/A", "description": "ORM prevents SQL injection."},
            {"id": "A05", "name": "Security Misconfiguration", "status": "WARN", "severity": "Low", "description": "CORS allows all origins.", "fix": "Restrict to production domain before launch."},
            {"id": "A07", "name": "Auth & Identification Failures", "status": "PASS", "severity": "N/A", "description": "JWT implementation is correct."},
            {"id": "A09", "name": "Logging & Monitoring", "status": "WARN", "severity": "Low", "description": "No centralized error logging.", "fix": "Add structured logging + error alerting."}
        ],
        "criticalIssues": 0, "highIssues": 0,
        "recommendations": ["Add rate limiting to auth endpoints", "Implement CSP headers", "Enable HTTPS + HSTS", "Add input validation middleware", "Set up Snyk dependency scanning"],
        "complianceNotes": "Add privacy policy, data deletion endpoint, and cookie consent for GDPR compliance before EU launch."
    }, indent=2)


def _copy_mock(idea: str) -> str:
    import json
    return json.dumps({
        "taglines": [f"The fastest way to {idea[:40]}", "Stop wasting time. Start building.", "Built for founders who move fast."],
        "heroSection": {"headline": f"The Smartest Way to {idea[:50]}", "subheadline": "Automate the complex parts. Focus on growth. Get started in minutes.", "cta": "Start Free Today"},
        "featuresSection": [
            {"title": "Instant Setup", "description": "Live in minutes, no technical knowledge required.", "icon": "⚡"},
            {"title": "AI-Powered", "description": "Automate repetitive work and surface real insights.", "icon": "🤖"},
            {"title": "Scales with You", "description": "From first user to first million — built to grow.", "icon": "📈"}
        ],
        "socialProof": "\"This saved us 3 weeks of work and closed our first deal.\" — Beta User",
        "pitchDeck": [
            {"slide": 1, "title": "Problem", "content": "Current solutions are too slow and too expensive for most founders.", "visualHint": "Pain point data"},
            {"slide": 2, "title": "Solution", "content": f"{idea} — faster, cheaper, and more complete.", "visualHint": "Product screenshot"},
            {"slide": 3, "title": "Market", "content": "$12B+ TAM. 15% annual growth. Underserved segment.", "visualHint": "TAM/SAM/SOM"},
            {"slide": 4, "title": "How It Works", "content": "3-step process: sign up → configure → launch.", "visualHint": "Flow diagram"},
            {"slide": 5, "title": "Business Model", "content": "Freemium → $49/mo Pro → $199/mo Team.", "visualHint": "Pricing table"},
            {"slide": 6, "title": "Traction", "content": "100 beta users, 4.8/5 NPS, 35% WoW growth.", "visualHint": "Growth chart"},
            {"slide": 7, "title": "GTM", "content": "Product Hunt → community → SEO → partnerships.", "visualHint": "GTM funnel"},
            {"slide": 8, "title": "Competition", "content": "Faster + cheaper + more complete than alternatives.", "visualHint": "Competitive matrix"},
            {"slide": 9, "title": "Team", "content": "Experienced founders with domain expertise.", "visualHint": "Team headshots"},
            {"slide": 10, "title": "Ask", "content": "Raising $500K seed to reach $1M ARR in 18 months.", "visualHint": "Use of funds"}
        ],
        "emailSubjectLines": [f"Early access: the future of {idea[:30]}", "We built what founders have been waiting for"],
        "productHuntTagline": f"AI-powered {idea[:35]} for modern founders"
    }, indent=2)


def _seo_mock(idea: str) -> str:
    import json
    w = idea[:20].strip()
    return json.dumps({
        "primaryKeywords": [f"{w} software", f"best {w} tool", f"AI {w}", f"{w} platform for startups", f"automated {w}"],
        "longTailKeywords": [f"how to {w} without coding", f"best {w} tool 2026", f"free {w} for founders", f"{w} vs alternatives", f"AI-powered {w} app"],
        "metaTags": {
            "title": f"Best {w.title()} Tool — AI-Powered & Free to Start",
            "description": f"Automate your {w} with AI. 10,000+ founders use it. Start free today.",
            "ogTitle": f"The #1 AI {w.title()} Platform",
            "ogDescription": f"Stop doing {w} manually — our AI does it in minutes."
        },
        "contentStrategy": [f"Pillar post: Ultimate guide to {w} (3000 words)", f"Comparison: Top 5 {w} tools 2026", "Case study: 80% time reduction with AI", "Weekly SEO newsletter"],
        "backlinkOpportunities": ["Product Hunt launch", "IndieHackers post", "Hacker News Show HN", "Relevant subreddits", "Industry newsletters"],
        "technicalSEO": ["Add schema.org SoftwareApplication markup", "Generate sitemap.xml", "Target LCP<2.5s, CLS<0.1"],
        "competitorKeywords": [f"{w} alternative", f"vs {w}"],
        "estimatedMonthlySearchVolume": "15,000–50,000 combined searches/month"
    }, indent=2)
