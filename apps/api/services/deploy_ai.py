"""
Bytez AI client — uses GPT-4.1 via Bytez API for fast, reliable completions.
No rate limits, no global serialization lock, no forced sleep between calls.
Replaces Groq LLaMA3 which caused 35s+ waits due to 429 TPM exhaustion.
"""
import asyncio
import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BYTEZ_BASE_URL = "https://api.bytez.com/models/v2"
DEFAULT_MODEL   = "openai/gpt-4.1"
MAX_RETRIES     = 3
RETRY_DELAY     = 2.0  # seconds between retries on transient errors


def _get_headers() -> dict:
    api_key = os.getenv("BYTEZ_API_KEY", "7d83a11bd95a2cba8d0484174add2ace")
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
        "lang": "python",
    }


async def run_agent_prompt(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8000,
) -> str:
    """
    Async Bytez/GPT-4.1 call.
    - No global lock — concurrent calls are safe (GPT-4.1 has no TPM issues)
    - No forced sleep — latency is purely network + model inference
    - Retries 3x on transient errors (5xx / network failures)
    """
    model = os.getenv("BYTEZ_MODEL", DEFAULT_MODEL)
    url   = f"{BYTEZ_BASE_URL}/{model}"

    payload = {
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "params": {
            "temperature": 0.7,
            # Note: Do NOT pass max_tokens or max_completion_tokens — Bytez/GPT-4.1
            # rejects requests that set both simultaneously. Default output limit is sufficient.
        },
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(url, headers=_get_headers(), json=payload)

            if response.status_code == 200:
                data = response.json()
                if data.get("error"):
                    raise Exception(f"Bytez model error: {data['error']}")
                output = data.get("output", "")
                logger.info(f"Bytez call success (attempt {attempt}, model={model})")
                # Bytez returns chat completion as {"role": "assistant", "content": "..."}
                if isinstance(output, dict):
                    return output.get("content", str(output))
                elif isinstance(output, list) and output:
                    first = output[0]
                    return first.get("content", str(first)) if isinstance(first, dict) else str(first)
                return str(output) if not isinstance(output, str) else output

            elif response.status_code in (500, 502, 503, 504):
                # Transient server error — retry
                last_error = Exception(f"Bytez {response.status_code}: {response.text[:200]}")
                logger.warning(f"Bytez transient error {response.status_code} (attempt {attempt}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * attempt)

            else:
                raise Exception(f"Bytez API error {response.status_code}: {response.text[:400]}")

        except httpx.TimeoutException as exc:
            last_error = exc
            logger.warning(f"Bytez timeout (attempt {attempt}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

        except Exception as exc:
            # Re-raise non-transient errors immediately
            if "Bytez model error" in str(exc) or "Bytez API error" in str(exc):
                raise
            last_error = exc
            logger.warning(f"Bytez unexpected error (attempt {attempt}): {exc}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    raise Exception(f"Bytez API failed after {MAX_RETRIES} retries. Last error: {last_error}")
