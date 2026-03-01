"""Security Reviewer Agent — OWASP Top 10 audit on generated code."""
import json
from workers.base_worker import BaseWorker


class SecurityReviewerWorker(BaseWorker):
    system_prompt = (
        "You are a cybersecurity expert specializing in web application security and OWASP standards. "
        "You perform thorough security audits on startup codebases. Respond ONLY with valid JSON."
    )

    def build_prompt(self, idea_text: str, context: dict) -> str:
        code = json.dumps(context.get("code_generator", {}), indent=2)
        return f"""Perform an OWASP Top 10 security audit on this MVP codebase.
Return a JSON object with these exact keys:
{{
  "overallScore": <integer 0-100>,
  "badge": "<SECURITY_CLEARED / SECURITY_WARNINGS / SECURITY_CRITICAL>",
  "owaspAudit": [
    {{
      "id": "<e.g. A01>",
      "name": "<OWASP category name>",
      "status": "<PASS / WARN / FAIL>",
      "severity": "<N/A / Low / Medium / High / Critical>",
      "description": "<finding>",
      "fix": "<recommended fix if applicable>"
    }}
  ],
  "criticalIssues": <integer count>,
  "highIssues": <integer count>,
  "recommendations": ["<security recommendation 1>", "<rec 2>", "<rec 3>"],
  "complianceNotes": "<GDPR/CCPA compliance status>"
}}

Codebase: {code[:3000]}"""  # Truncate to avoid token limits
