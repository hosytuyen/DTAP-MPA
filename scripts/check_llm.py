#!/usr/bin/env python3
"""Check the evaluation model adapter with a harmless tool-call round trip."""

import argparse
import asyncio
import os
from pathlib import Path
import secrets
import sys

# Allow invocation from a source checkout without changing PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def check(args):
    os.environ["OPENAI_BASE_URL"] = args.base_url.rstrip("/")
    os.environ.setdefault("OPENAI_API_KEY", "dummy")
    os.environ["DTAP_OPENAI_API"] = "chat_completions"

    from agents import Agent, ModelSettings, RunConfig, Runner, function_tool
    from agent.openaisdk.src.agent import _build_model

    calls = []
    receipt = "DTAP-" + secrets.token_hex(8)

    @function_tool
    def get_check_receipt(label: str) -> str:
        """Fetch the secret verification receipt for the label llm-check."""
        calls.append(label)
        if label != "llm-check":
            raise ValueError("Expected label llm-check")
        return receipt

    print(f"Endpoint: {args.base_url}", flush=True)
    print(f"Model: {args.model}", flush=True)
    print("Checking automatic tool selection, tool execution, and final response...", flush=True)
    agent = Agent(
        name="LLM interface check",
        instructions=(
            "Call get_check_receipt with label llm-check to obtain the secret receipt. "
            "Then reply with exactly that receipt. Never invent a receipt."
        ),
        model=_build_model(args.model),
        tools=[get_check_receipt],
        model_settings=ModelSettings(
            tool_choice="auto",
            max_tokens=args.max_tokens,
        ),
    )
    result = await asyncio.wait_for(
        Runner.run(
            agent,
            "Fetch the verification receipt now.",
            max_turns=4,
            run_config=RunConfig(tracing_disabled=True),
        ),
        timeout=args.timeout,
    )
    if not calls:
        raise RuntimeError("The model replied without calling the tool.")
    if any(label != "llm-check" for label in calls):
        raise RuntimeError(f"Incorrect tool arguments: {calls!r}")
    if receipt not in str(result.final_output):
        raise RuntimeError("The final response did not contain the receipt returned by the tool.")
    print("PASS: the repo's OpenAI adapter completed a tool-call round trip.")
    print("This checks the LLM interface; Docker, CRM, and MCP startup are not tested.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://localhost:6008/v1"))
    parser.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B")
    parser.add_argument("--timeout", type=float, default=120, help="Total timeout in seconds")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Output budget per request, including reasoning")
    args = parser.parse_args()
    try:
        asyncio.run(check(args))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check the SSH tunnel, model name, API key, and vLLM tool-calling flags. "
            "If output is truncated, increase --max-tokens.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
