"""Product Architect Agent — tech stack, system design, data model, API contracts."""
import json
from workers.base_worker import BaseWorker


class ProductArchitectWorker(BaseWorker):
    system_prompt = (
        "You are a senior software architect specializing in scalable SaaS systems. "
        "You recommend practical, modern tech stacks for startup MVPs. Respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        validation = json.dumps(context.get("idea_validator", {}), indent=2)
        return f"""Design the technical architecture for this startup MVP.
Return a JSON object with these exact keys:
{{
  "recommendedStack": {{
    "frontend": "<framework>",
    "backend": "<framework + language>",
    "database": "<primary DB>",
    "cache": "<cache solution>",
    "hosting": "<recommended platform>"
  }},
  "systemDesign": "<2-3 sentence architecture description>",
  "coreFeatures": ["<feature 1>", "<feature 2>", "<feature 3>"],
  "dataModel": {{
    "tables": ["<table1: key fields>", "<table2: key fields>"]
  }},
  "apiEndpoints": [
    {{"method": "POST", "path": "/api/...", "description": "<what it does>"}},
    {{"method": "GET", "path": "/api/...", "description": "<what it does>"}}
  ],
  "scalabilityNotes": "<how the system scales>"
}}

Idea: {idea_text}
Validation: {validation}"""
