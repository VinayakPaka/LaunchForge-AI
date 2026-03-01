"""Code Generator Agent — generates full MVP code structure."""
import json
from workers.base_worker import BaseWorker


class CodeGeneratorWorker(BaseWorker):
    system_prompt = (
        "You are an expert full-stack developer who generates clean, production-ready MVP code. "
        "You generate complete, runnable code with comments. Respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        arch = json.dumps(context.get("product_architect", {}), indent=2)
        strategy = json.dumps(context.get("strategy_planner", {}), indent=2)
        return f"""Generate an MVP codebase for this startup idea.
Return a JSON object with these exact keys:
{{
  "projectName": "<slug-name>",
  "techStack": "<stack summary>",
  "files": [
    {{
      "path": "<file path e.g. src/app/page.tsx>",
      "content": "<complete file content>",
      "description": "<what this file does>"
    }}
  ],
  "setupInstructions": ["<step 1>", "<step 2>", "<step 3>"],
  "envVariables": ["<VAR_NAME=description>"],
  "testSuite": "<brief description of test approach>",
  "readmeSummary": "<2-3 sentence project description>"
}}

Generate at least 5 key files including: main app entry, a core feature component, API route, data model, and README.

Idea: {idea_text}
Architecture: {arch}
Strategy: {strategy}"""
