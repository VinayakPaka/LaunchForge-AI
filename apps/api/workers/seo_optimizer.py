"""SEO Optimizer Agent — keyword research, meta tags, content strategy."""
import json
from workers.base_worker import BaseWorker


class SEOOptimizerWorker(BaseWorker):
    system_prompt = (
        "You are an SEO expert specializing in SaaS and startup growth. "
        "You create data-driven SEO strategies for new products. Respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        validation = json.dumps(context.get("idea_validator", {}), indent=2)
        copy = json.dumps(context.get("copywriter", {}), indent=2)
        return f"""Create a comprehensive SEO strategy for this startup.
Return a JSON object with these exact keys:
{{
  "primaryKeywords": ["<keyword 1>", "<keyword 2>", "<keyword 3>", "<keyword 4>", "<keyword 5>"],
  "longTailKeywords": ["<phrase 1>", "<phrase 2>", "<phrase 3>", "<phrase 4>", "<phrase 5>"],
  "metaTags": {{
    "title": "<SEO page title under 60 chars>",
    "description": "<meta description under 160 chars>",
    "ogTitle": "<OG title>",
    "ogDescription": "<OG description>"
  }},
  "contentStrategy": ["<content piece 1>", "<content piece 2>", "<content piece 3>"],
  "backlinkOpportunities": ["<source 1>", "<source 2>", "<source 3>"],
  "technicalSEO": ["<technical recommendation 1>", "<rec 2>"],
  "competitorKeywords": ["<competitor keyword 1>", "<competitor keyword 2>"],
  "estimatedMonthlySearchVolume": "<total keyword volume estimate>"
}}

Idea: {idea_text}
Validation: {validation}"""
