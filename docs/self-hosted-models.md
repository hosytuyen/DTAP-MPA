# Self-hosted models with the OpenAI SDK backend

The `openaisdk` backend supports OpenAI-compatible servers such as vLLM.
An Anthropic `/v1/messages` endpoint alone is insufficient for this backend;
the server must also expose `/v1/chat/completions` and support automatic tool calls.

For a Qwen server forwarded to localhost port 6008:

```bash
source .venv/bin/activate
export OPENAI_BASE_URL=http://localhost:6008/v1
export OPENAI_API_KEY=dummy
export DTAP_OPENAI_API=chat_completions

python eval/evaluation.py \
  --task-list benchmark/crm/benign.jsonl \
  --agent-type openaisdk \
  --model Qwen/Qwen3.6-35B-A3B \
  --max-parallel 1
```

Keep the port forwarding session and Docker Desktop running. Use the server's
actual key instead of `dummy` if authentication is enabled. Start with one
parallel task, then increase concurrency as server capacity allows.

You can also put these three environment variables in the repo root `.env`
instead of exporting them. Evaluation loads that file automatically, including
when invoked with `dtap eval`. Existing shell variables take precedence over
values in `.env`.

`DTAP_OPENAI_API` accepts `auto` (default), `chat_completions`, or `responses`.
Auto selects Chat Completions when `OPENAI_BASE_URL` is set, and the SDK's
default Responses API otherwise. Inline subagents use the same selection.
Custom endpoints that support Responses can explicitly select `responses`.

## Enable server-side tool calling

If vLLM returns `"auto" tool choice requires --enable-auto-tool-choice and
--tool-call-parser to be set`, add these flags to the server launch command:

```bash
--enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3
```

Keep your existing GPU, port, and model settings. Parser names depend on vLLM
version; newer releases also document `qwen3_xml` for this tool format.
Check your installed version's supported parsers. References:
[vLLM tool calling](https://docs.vllm.ai/en/latest/features/tool_calling/) and
[Qwen3.5/3.6 serving guide](https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html).

The client cannot enable these server flags. Verify that a request with tools
and `tool_choice: "auto"` produces a structured `tool_calls` response before
running the benchmark. Text-only chat success does not verify tool calling.
