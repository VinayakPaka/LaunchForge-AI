"""Base class for all agent workers."""
from abc import ABC, abstractmethod
from services.deploy_ai import run_agent_prompt


class BaseWorker(ABC):
    """Each worker defines its system prompt and builds the user prompt from context."""

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def build_prompt(self, idea_text: str, context: dict) -> str:
        ...

    async def run(self, idea_text: str, context: dict) -> dict:
        """Execute the agent and return parsed result dict."""
        import json
        user_prompt = self.build_prompt(idea_text, context)
        raw = await run_agent_prompt(self.system_prompt, user_prompt)
        # Attempt to parse JSON; fall back to wrapping raw text
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(cleaned)
        except Exception:
            return {"rawOutput": raw}
