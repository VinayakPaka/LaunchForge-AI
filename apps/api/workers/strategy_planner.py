"""Strategy Planner Agent — monetization model, GTM strategy, pricing tiers."""
import json
from workers.base_worker import BaseWorker


class StrategyPlannerWorker(BaseWorker):
    system_prompt = (
        "You are a startup strategy expert specializing in go-to-market planning, "
        "monetization models, and competitive positioning. Respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        validation = json.dumps(context.get("idea_validator", {}), indent=2)
        return f"""Based on the validated startup idea below, create a comprehensive strategy.
Return a JSON object with these exact keys:
{{
  "monetizationModel": "<primary model e.g. SaaS, marketplace, freemium>",
  "pricingTiers": {{"free": "<tier details>", "pro": "<price + features>", "enterprise": "<price + features>"}},
  "gtmStrategy": "<3-sentence GTM strategy>",
  "targetChannels": ["<channel 1>", "<channel 2>", "<channel 3>", "<channel 4>"],
  "launchTimeline": {{"week1": "<action>", "month1": "<action>", "month3": "<action>"}},
  "competitivePositioning": "<unique differentiator in one sentence>",
  "revenueProjection": {{"month6": "<ARR estimate>", "year1": "<ARR estimate>"}}
}}

Idea: {idea_text}
Validation Report: {validation}"""
