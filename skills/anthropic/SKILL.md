---
name: anthropic
description: "Integrates with the Anthropic Claude API to send messages, stream responses, handle multi-turn conversations, and build AI-powered applications. Use when asked to: call Claude API, send a message to Claude, stream Claude responses, set up Anthropic client, build a chatbot with Claude, generate text with Claude, use claude-opus or claude-sonnet models, implement multi-turn conversation with Claude, add AI to my Python app using Anthropic."
license: Apache-2.0
compatibility:
- node >= 16
metadata:
  author: SharpSkills
  version: 1.0.0
  category: ai
  tags: [anthropic, claude, llm, ai, chatbot, streaming, python]
---

# Anthropic Skill

## Quick Start

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # default; can omit if env var set
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude!"}],
)
print(message.content[0].text)
```

## When to Use

Use this skill when asked to:
- Call the Claude / Anthropic API from Python
- Send a message to Claude and get a response
- Stream Claude completions token-by-token
- Build a multi-turn chatbot with conversation history
- Set up an Anthropic API client with environment-based credentials
- Generate text, summaries, or analysis with a Claude model
- Switch between claude-opus, claude-sonnet, or claude-haiku models
- Add system prompts or personas to a Claude conversation
- Handle rate-limit or API errors when calling Anthropic
- Use vision / image inputs with Claude

## Core Patterns

### Pattern 1: Basic Message (Source: official)

Send a single user message and print the text response.

```python
import os
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from environment

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain quantum entanglement in one paragraph."}
    ],
)

print(response.content[0].text)
print(f"\nUsage — input: {response.usage.input_tokens}, output: {response.usage.output_tokens}")
```

### Pattern 2: Multi-Turn Conversation (Source: official)

Maintain conversation history manually by appending messages.

```python
from anthropic import Anthropic

client = Anthropic()

conversation = []

def chat(user_input: str) -> str:
    conversation.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system="You are a helpful assistant. Be concise.",
        messages=conversation,
    )

    assistant_text = response.content[0].text
    conversation.append({"role": "assistant", "content": assistant_text})
    return assistant_text

print(chat("What is the capital of France?"))
print(chat("What is its population?"))  # Claude remembers context
```

### Pattern 3: Streaming Responses (Source: official)

Stream tokens as they are generated to avoid waiting for full completion.

```python
from anthropic import Anthropic

client = Anthropic()

with client.messages.stream(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a short poem about the ocean."}],
) as stream:
    for text_chunk in stream.text_stream:
        print(text_chunk, end="", flush=True)

# Access the final complete message after streaming
final_message = stream.get_final_message()
print(f"\n\nStop reason: {final_message.stop_reason}")
```

### Pattern 4: System Prompt + Vision (Source: official)

Pass a system prompt and an image URL for multimodal tasks.

```python
import base64
import httpx
from anthropic import Anthropic

client = Anthropic()

# Fetch and encode image as base64
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
image_data = base64.standard_b64encode(httpx.get(image_url).content).decode("utf-8")

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system="You are an expert image analyst. Describe images accurately and concisely.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data,
                    },
                },
                {"type": "text", "text": "What do you see in this image?"},
            ],
        }
    ],
)

print(response.content[0].text)
```

### Pattern 5: Async Client (Source: official)

Use `AsyncAnthropic` for async frameworks (FastAPI, asyncio, etc.).

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def generate(prompt: str) -> str:
    response = await client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text

async def main():
    results = await asyncio.gather(
        generate("Summarize the theory of relativity."),
        generate("What is machine learning?"),
    )
    for r in results:
        print(r, "\n---")

asyncio.run(main())
```

### Pattern 6: Error Handling (Source: community)

Handle rate limits and API errors gracefully to avoid unhandled crashes in production.

```python
# Source: community
# Tested: SharpSkill
import time
import anthropic
from anthropic import (
    Anthropic,
    APIConnectionError,
    APIStatusError,
    RateLimitError,
)

client = Anthropic()

def call_with_retry(messages: list, max_retries: int = 3, backoff: float = 2.0) -> str:
    """Call Claude with exponential backoff on rate limit errors."""
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=messages,
            )
            return response.content[0].text

        except RateLimitError as e:
            wait = backoff ** attempt
            print(f"Rate limited. Waiting {wait}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait)

        except APIConnectionError as e:
            print(f"Connection error: {e}. Retrying...")
            time.sleep(backoff)

        except APIStatusError as e:
            # 4xx errors (bad request, auth failure) — do not retry
            print(f"API error {e.status_code}: {e.message}")
            raise

    raise RuntimeError(f"Failed after {max_retries} retries.")

result = call_with_retry([{"role": "user", "content": "Hello!"}])
print(result)
```

### Pattern 7: Tool Use / Function Calling (Source: official)

Define tools for Claude to call and handle tool results in a loop.

```python
from anthropic import Anthropic

client = Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Returns current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    }
]

def get_weather(city: str) -> str:
    # Replace with real weather API call
    return f"Sunny, 22°C in {city}"

messages = [{"role": "user", "content": "What's the weather in Paris?"}]

while True:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    if response.stop_reason == "end_turn":
        print(response.content[0].text)
        break

    if response.stop_reason == "tool_use":
        tool_use = next(b for b in response.content if b.type == "tool_use")
        tool_result = get_weather(**tool_use.input)

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result,
                }
            ],
        })
```

## Production Notes

1. **API key never in source code** — Always load from environment (`ANTHROPIC_API_KEY`) or a secrets manager (AWS Secrets Manager, HashiCorp Vault). Committing keys triggers automatic revocation by Anthropic.  
   Source: Anthropic official docs

2. **`max_tokens` is required** — Unlike some LLM SDKs, Anthropic's `messages.create` will raise a `BadRequestError` if `max_tokens` is omitted entirely. Always set a sensible upper bound per your use case.  
   Source: Anthropic official docs

3. **Rate limits cause silent data loss in naive loops** — Production pipelines that call the API in tight loops without backoff drop requests without obvious errors. Use exponential backoff (see Pattern 6). Anthropic's default tier is ~50 RPM.  
   Source: GitHub Issues / community reports

4. **Model names change** — Hardcoded model strings like `claude-2` become deprecated. Pin to a dated alias (e.g., `claude-opus-4-5`) and monitor the [model deprecation page](https://docs.anthropic.com/en/docs/about-claude/models) in CI.  
   Source: Anthropic official docs

5. **Streaming + asyncio mix** — Mixing `client.messages.stream()` (sync) inside an async function causes event-loop blocking. Use `AsyncAnthropic` with `async with client.messages.stream()` in async contexts.  
   Source: community / GitHub Issues

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `AuthenticationError: 401` on first call | `ANTHROPIC_API_KEY` not set or has leading/trailing whitespace | `export ANTHROPIC_API_KEY="sk-ant-..."` — strip whitespace; verify with `echo $ANTHROPIC_API_KEY` |
| `BadRequestError: max_tokens` missing | `max_tokens` omitted from `messages.create()` | Always pass `max_tokens`; use 1024 as a safe default |
| `RateLimitError: 429` in batch jobs | Too many requests per minute for your tier | Implement exponential backoff; request a rate-limit increase via Anthropic console |
| `response.content[0].text` raises `IndexError` | `stop_reason` is `"tool_use"` — content block is `ToolUseBlock`, not `TextBlock` | Check `response.stop_reason` and handle `"tool_use"` branches before accessing `.text` |
| Streaming hangs indefinitely | Network timeout or large `max_tokens` with slow generation | Set `httpx` timeout via `Anthropic(timeout=60.0)`; reduce `max_tokens` |
| `APIConnectionError` in Docker/CI | DNS resolution failure or missing egress rules to `api.anthropic.com:443` | Whitelist `api.anthropic.com` port 443; verify with `curl https://api.anthropic.com` |

## Pre-Deploy Checklist

- [ ] `ANTHROPIC_API_KEY` stored in environment variables or secrets manager — never in code or `.env` committed to VCS
- [ ] `max_tokens` explicitly set on every `messages.create()` call
- [ ] Exponential backoff implemented for `RateLimitError` and `APIConnectionError`
- [ ] Model string pinned to a dated/versioned alias and reviewed against Anthropic's deprecation schedule
- [ ] `stop_reason` checked before accessing `response.content[0].text` (handle `"tool_use"` and `"max_tokens"`)
- [ ] Async code uses `AsyncAnthropic` — never calls sync streaming inside an `async` function
- [ ] Token usage (`response.usage`) logged per request for cost monitoring and alerting

## Troubleshooting

**Error: `anthropic.AuthenticationError: 401 {"type":"error","error":{"type":"authentication_error"}}`**  
Cause: API key is missing, malformed, or revoked.  
Fix: Run `echo $ANTHROPIC_API_KEY` to confirm it is set. Re-generate the key at console.anthropic.com if needed. Ensure no extra whitespace in the value.

**Error: `IndexError: list index out of range` on `response.content[0].text`**  
Cause: Claude returned a `tool_use` stop reason; the first content block is a `ToolUseBlock`, not a `TextBlock`.  
Fix: Check `response.stop_reason == "end_turn"` before accessing `.text`, and handle `"tool_use"` blocks separately.

**Error: `httpx.ReadTimeout` during long completions**  
Cause: Default timeout is too short for large `max_tokens` values.  
Fix: Increase the timeout: `Anthropic(timeout=120.0)` or use streaming to receive tokens incrementally.

**Error: `RateLimitError: 429` in production batch**  
Cause: Exceeded requests-per-minute limit on your Anthropic tier.  
Fix: Add exponential backoff (see Pattern 6); consider parallelism limits; apply for a higher rate limit tier at console.anthropic.com.

## Resources

- Docs: https://docs.anthropic.com/en/api/
- SDK Docs: https://platform.claude.com/docs/en/api/sdks/python
- Models Reference: https://docs.anthropic.com/en/docs/about-claude/models
- GitHub: https://github.com/anthropics/anthropic-sdk-python
- Console / API Keys: https://console.anthropic.com/