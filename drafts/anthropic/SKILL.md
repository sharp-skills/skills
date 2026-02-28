---
name: anthropic
description: "Provides patterns for integrating with the Anthropic Claude API via the official Python SDK. Use when user asks to: call Claude API, send messages to Claude, use claude-opus or claude-sonnet models, build a chatbot with Claude, stream Claude responses, handle Anthropic API errors, set system prompts for Claude, count tokens before sending, build a multi-turn conversation with Claude, use tool use / function calling with Claude."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: ai
  tags: [anthropic, claude, llm, ai, chatbot, streaming, tool-use]
---

# Anthropic Skill

## Quick Start

```bash
pip install anthropic
```

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # default; can be omitted if env var is set
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
)
print(message.content[0].text)
```

## When to Use

Use this skill when asked to:
- "Call the Claude API" / "send a message to Claude"
- "Use claude-opus, claude-sonnet, or claude-haiku in my app"
- "Stream a response from Claude"
- "Set a system prompt for Claude"
- "Build a multi-turn conversation / chatbot with Claude"
- "Use tool use or function calling with Claude"
- "Count tokens before sending to Claude"
- "Handle Anthropic API rate limits or errors"
- "Switch from OpenAI to Anthropic / migrate to Claude"
- "Use the Anthropic async client"

## Core Patterns

### Pattern 1: System Prompt + Multi-Turn Conversation (Source: official)

System prompts steer Claude's persona and behavior. Maintain conversation history manually — the API is stateless.

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

conversation_history = []

def chat(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system="You are a helpful senior software engineer. Be concise.",
        messages=conversation_history,
    )

    assistant_message = response.content[0].text
    conversation_history.append({"role": "assistant", "content": assistant_message})
    return assistant_message

print(chat("What is a context manager in Python?"))
print(chat("Show me a practical example."))
```

### Pattern 2: Streaming Responses (Source: official)

Use streaming for long responses or real-time UX. Stream events arrive as `text_delta` chunks.

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with client.messages.stream(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku about Python."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Access the final complete message after streaming
final_message = stream.get_final_message()
print(f"\n\nInput tokens:  {final_message.usage.input_tokens}")
print(f"Output tokens: {final_message.usage.output_tokens}")
```

### Pattern 3: Tool Use / Function Calling (Source: official)

Claude can call tools you define. The loop: send tools → Claude returns `tool_use` block → you run the tool → send result back.

```python
import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'London'"},
            },
            "required": ["city"],
        },
    }
]

def get_weather(city: str) -> str:
    # Replace with real API call
    return f"Sunny, 22°C in {city}"

messages = [{"role": "user", "content": "What's the weather in Paris?"}]

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)

# Agentic loop — handle tool_use blocks
while response.stop_reason == "tool_use":
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = get_weather(**block.input)  # dispatch by block.name in production
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

print(response.content[0].text)
```

### Pattern 4: Async Client (Source: official)

Use `AsyncAnthropic` inside async applications (FastAPI, async scripts, etc.).

```python
import os
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

async def main():
    message = await client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Explain async/await in one sentence."}],
    )
    print(message.content[0].text)

asyncio.run(main())
```

### Pattern 5: Token Counting Before Sending (Source: official)

Count tokens before the request to avoid exceeding context limits or to estimate cost.

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

messages = [{"role": "user", "content": "Summarize the French Revolution in detail."}]

response = client.messages.count_tokens(
    model="claude-opus-4-5",
    system="You are a historian.",
    messages=messages,
)

print(f"Estimated input tokens: {response.input_tokens}")
# Gate on context window (claude-opus-4-5 supports 200k tokens)
if response.input_tokens > 190_000:
    raise ValueError("Prompt too large — truncate before sending.")
```

### Pattern 6: Robust Error Handling (Source: community)

Anthropic errors are typed. Always catch `RateLimitError` and `APIStatusError` separately in production; naive bare `except` swallows rate-limit signals, causing infinite retry loops.

```python
import os
import time
from anthropic import Anthropic, RateLimitError, APIStatusError, APIConnectionError

# Source: community / Tested: SharpSkill
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def call_with_retry(messages: list, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=messages,
            )
            return response.content[0].text

        except RateLimitError as e:
            wait = 2 ** attempt  # exponential back-off: 1s, 2s, 4s
            print(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)

        except APIConnectionError as e:
            print(f"Network error: {e}. Retrying…")
            time.sleep(1)

        except APIStatusError as e:
            # 400 = bad request (prompt/model mismatch) — do NOT retry
            if e.status_code == 400:
                raise ValueError(f"Bad request — check model name and message format: {e.message}") from e
            # 529 = overloaded; 500 = server error — safe to retry
            if e.status_code in (500, 529):
                time.sleep(2 ** attempt)
            else:
                raise  # 401 auth, 403 forbidden — no point retrying

    raise RuntimeError(f"Failed after {max_retries} retries.")

result = call_with_retry([{"role": "user", "content": "Hello!"}])
print(result)
```

## Production Notes

1. **API key must be in the environment — never hardcoded.** Use `ANTHROPIC_API_KEY` env var or a secrets manager. The SDK reads it automatically; passing it explicitly is optional. Source: official docs.

2. **`max_tokens` is required and caps output, not context.** Forgetting it raises a `400` immediately. Set it based on expected output length; it does not affect pricing for unused tokens — only tokens actually generated are billed. Source: official docs.

3. **Message array roles must alternate `user` / `assistant`.** Two consecutive `user` messages throw a `400 {"error":"messages must alternate between 'user' and 'assistant' roles"}`. Always append the assistant response before the next user turn. Source: GitHub Issues, community reports.

4. **Model names change — pin explicitly.** Using `"claude-opus-4"` without the full versioned name can resolve to a deprecated model or raise a 404. Always use the full dated model string (e.g., `"claude-opus-4-5"`). Check [docs.anthropic.com/en/docs/about-claude/models](https://docs.anthropic.com/en/docs/about-claude/models) for the current list. Source: community reports.

5. **Streaming and `get_final_message()` — consume the stream fully before accessing metadata.** Accessing `stream.get_final_message()` or `stream.usage` before the `with` block exits raises a `StreamNotReadError`. Always place metadata access after the loop or after the `with` block closes. Source: community / Tested: SharpSkill.

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `400 messages must alternate` | Two consecutive `user` or `assistant` messages in history | Ensure roles alternate; append assistant reply before next user message |
| `401 AuthenticationError` | Missing or invalid `ANTHROPIC_API_KEY` | Set env var correctly; confirm key is active in console.anthropic.com |
| `404 model not found` | Short/deprecated model name (e.g., `claude-3`) | Use full versioned model string from the official models page |
| `RateLimitError` with instant failure | No retry logic; bare `except Exception` swallowed | Add typed `RateLimitError` catch with exponential back-off |
| Stream metadata raises `StreamNotReadError` | Accessing `get_final_message()` inside the `with` block before stream completes | Move metadata access outside / after the `with` block |

## Pre-Deploy Checklist

- [ ] `ANTHROPIC_API_KEY` stored in environment / secrets manager — not in source code
- [ ] Full versioned model name used (e.g., `claude-opus-4-5`) — confirmed against official models page
- [ ] `max_tokens` explicitly set and sized appropriately for expected output
- [ ] Message history validated to alternate `user` / `assistant` roles before every API call
- [ ] `RateLimitError` caught separately with exponential back-off (not bare `except`)
- [ ] Token count checked before sending large prompts (`client.messages.count_tokens`)
- [ ] Streaming response fully consumed before accessing `.get_final_message()` or `.usage`

## Troubleshooting

**Error: `anthropic.AuthenticationError: 401 {"type":"error","error":{"type":"authentication_error"}}`**
Cause: API key is missing, revoked, or malformed.
Fix: Run `echo $ANTHROPIC_API_KEY` to verify it is set. Regenerate at console.anthropic.com if needed. Ensure no leading/trailing whitespace in the value.

**Error: `anthropic.BadRequestError: 400 messages: roles must alternate`**
Cause: The messages array contains two consecutive entries with the same role.
Fix: After each `client.messages.create` call, append `{"role": "assistant", "content": response.content[0].text}` to your history before appending the next user message.

**Error: `anthropic.RateLimitError: 429 Request rate limit reached`**
Cause: Too many requests per minute for your tier.
Fix: Implement exponential back-off (see Pattern 6). Check your rate limits at console.anthropic.com and request an increase if needed.

**Error: `StreamNotReadError` when accessing stream metadata**
Cause: `stream.get_final_message()` called before the stream generator is exhausted.
Fix: Place all metadata access after the `with client.messages.stream(...) as stream:` block closes, not inside it.

## Resources

- Docs: https://docs.anthropic.com/en/api/
- Models list: https://docs.anthropic.com/en/docs/about-claude/models
- Python SDK GitHub: https://github.com/anthropics/anthropic-sdk-python
- API Console: https://console.anthropic.com