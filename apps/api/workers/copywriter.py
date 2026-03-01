"""Copywriter Agent — landing page copy, pitch deck, taglines."""
import json
from workers.base_worker import BaseWorker


class CopywriterWorker(BaseWorker):
    system_prompt = (
        "You are a world-class startup copywriter and pitch deck creator. "
        "You write compelling, conversion-focused copy for tech startups. Respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        validation = json.dumps(context.get("idea_validator", {}), indent=2)
        strategy = json.dumps(context.get("strategy_planner", {}), indent=2)
        return f"""Create complete marketing copy for this startup.
Return a JSON object with these exact keys:
{{
  "taglines": ["<tagline option 1>", "<tagline option 2>", "<tagline option 3>"],
  "heroSection": {{
    "headline": "<main headline>",
    "subheadline": "<supporting headline>",
    "cta": "<call-to-action button text>"
  }},
  "featuresSection": [
    {{"title": "<feature name>", "description": "<one-sentence benefit>", "icon": "<emoji>"}}
  ],
  "socialProof": "<mock testimonial or stat>",
  "pitchDeck": [
    {{"slide": 1, "title": "<slide title>", "content": "<key message>", "visualHint": "<what to show>"}}
  ],
  "emailSubjectLines": ["<email 1 subject>", "<email 2 subject>"],
  "productHuntTagline": "<40-char Product Hunt tagline>"
}}

Include 10 pitch deck slides covering: Problem, Solution, Market, Product, Business Model, Traction, Team, Roadmap, Financials, Ask.

Idea: {idea_text}
Validation: {validation}
Strategy: {strategy}"""
