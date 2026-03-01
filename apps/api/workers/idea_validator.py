"""Idea Validator Agent — refines raw idea, validates market fit, scores opportunity."""
from workers.base_worker import BaseWorker


class IdeaValidatorWorker(BaseWorker):
    system_prompt = (
        "You are an expert startup idea validator with deep knowledge of market analysis, "
        "product-market fit, and competitive landscapes. You respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        return f"""Analyze this startup idea and return a JSON object with these exact keys:
{{
  "refinedIdea": "<one-sentence refined version>",
  "problemStatement": "<clear problem being solved>",
  "targetAudience": "<specific target users>",
  "proposedSolution": "<concise solution description>",
  "marketOpportunity": "<market opportunity summary>",
  "marketScore": <integer 0-100>,
  "tam": "<Total Addressable Market estimate>",
  "sam": "<Serviceable Addressable Market>",
  "som": "<Serviceable Obtainable Market>",
  "competitors": ["<competitor 1>", "<competitor 2>", "<competitor 3>"],
  "riskFlags": ["<risk 1>", "<risk 2>"],
  "recommendation": "<PROCEED / PIVOT / STOP with one-sentence reason>"
}}

Startup idea: {idea_text}"""
