---
name: openai
description: "Integrates OpenAI's REST API (GPT models, embeddings, images, audio, files, fine-tuning) into TypeScript/JavaScript and Python applications. Use when asked to: call the OpenAI API, generate text with GPT, stream chat completions, upload files for fine-tuning, create embeddings, generate images with DALL-E, transcribe audio with Whisper, handle OpenAI API errors, or verify OpenAI webhooks."
license: Apache-2.0
metadata:
  author: SharpSkills
  version: 1.0.0
  category: ai
  tags: [openai, gpt, llm, chat-completions, responses-api, embeddings, streaming, fine-tuning]
---

# OpenAI Skill

## Quick Start

```bash
npm install openai          # Node/TypeScript
pip install openai          # Python
```

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env['OPENAI_API_KEY'], // default; can be omitted
});

// Responses API (primary, recommended)
const response = await client.responses.create({
  model: 'gpt-4o',
  instructions: 'You are a helpful assistant.',
  input: 'Explain async/await in JavaScript.',
});
console.log(response.output_text);
```

```python
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from env automatically

response = client.responses.create(
    model="gpt-4o",
    instructions="You are a helpful assistant.",
    input="Explain async/await in JavaScript.",
)
print(response.output_text)
```

## When to Use

Use this skill when asked to:
- Call the OpenAI API or integrate GPT into an application
- Generate, stream, or process text completions with GPT-4o / GPT-4
- Send multimodal (vision) requests with images and text
- Upload files and run fine-tuning jobs
- Create vector embeddings for semantic search or RAG pipelines
- Generate images using DALL-E or transcribe audio with Whisper
- Handle context-length errors or rate-limit errors from OpenAI
- Verify and parse incoming OpenAI webhook payloads
- Build async or concurrent OpenAI request pipelines in Python or Node
- Proxy or route OpenAI API traffic through a custom endpoint

## Core Patterns

### Pattern 1: Streaming Responses (Source: official)

Use streaming when latency matters — tokens are yielded as they are generated.

```typescript
import OpenAI from 'openai';

const client = new OpenAI();

const stream = await client.responses.create({
  model: 'gpt-4o',
  input: 'Write a haiku about distributed systems.',
  stream: true,
});

for await (const event of stream) {
  // event.type differentiates delta vs. completion events
  process.stdout.write(event?.delta ?? '');
}
```

```python
from openai import OpenAI

client = OpenAI()

with client.responses.stream(
    model="gpt-4o",
    input="Write a haiku about distributed systems.",
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Pattern 2: Chat Completions API (Source: official)

The Chat Completions API is the established standard and remains fully supported.

```typescript
import OpenAI from 'openai';

const client = new OpenAI();

const completion = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'system', content: 'You are a senior TypeScript engineer.' },
    { role: 'user', content: 'What is the difference between type and interface?' },
  ],
  temperature: 0.2,
  max_tokens: 512,
});

console.log(completion.choices[0].message.content);
```

```python
from openai import OpenAI

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a senior Python engineer."},
        {"role": "user", "content": "Explain Python's GIL in plain English."},
    ],
    temperature=0.2,
    max_tokens=512,
)
print(completion.choices[0].message.content)
```

### Pattern 3: Vision — Multimodal Input (Source: official)

Pass images alongside text for analysis, OCR, or visual QA tasks.

```python
import base64
from openai import OpenAI

client = OpenAI()

# Option A: public URL
response = client.responses.create(
    model="gpt-4o",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "What is in this image?"},
            {"type": "input_image", "image_url": "https://example.com/photo.jpg"},
        ],
    }],
)

# Option B: base64-encoded local file
with open("diagram.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.responses.create(
    model="gpt-4o",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Describe this architecture diagram."},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
        ],
    }],
)
print(response.output_text)
```

### Pattern 4: File Uploads and Fine-Tuning (Source: official)

Upload training data, then kick off a fine-tuning job.

```typescript
import fs from 'fs';
import OpenAI, { toFile } from 'openai';

const client = new OpenAI();

// Upload a JSONL training file
const uploaded = await client.files.create({
  file: fs.createReadStream('training_data.jsonl'),
  purpose: 'fine-tune',
});

// Create the fine-tuning job
const job = await client.fineTuning.jobs.create({
  training_file: uploaded.id,
  model: 'gpt-4o-mini',
});

console.log('Fine-tune job ID:', job.id);

// Poll status
const status = await client.fineTuning.jobs.retrieve(job.id);
console.log('Status:', status.status);
```

### Pattern 5: Embeddings (Source: official)

Generate dense vector embeddings for semantic search and RAG.

```python
from openai import OpenAI

client = OpenAI()

texts = [
    "OpenAI provides powerful language models.",
    "Embeddings enable semantic similarity search.",
]

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts,
)

for i, item in enumerate(response.data):
    print(f"Text {i}: vector dim={len(item.embedding)}")
    # Store item.embedding in your vector DB (Pinecone, pgvector, etc.)
```

### Pattern 6: Async Client — Python (Source: official)

Use `AsyncOpenAI` for non-blocking I/O in async frameworks (FastAPI, asyncio).

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def summarize(text: str) -> str:
    response = await client.responses.create(
        model="gpt-4o",
        instructions="Summarize the following text in one sentence.",
        input=text,
    )
    return response.output_text

async def main():
    # Run multiple requests concurrently
    results = await asyncio.gather(
        summarize("Long article about climate change..."),
        summarize("Long article about quantum computing..."),
    )
    for r in results:
        print(r)

asyncio.run(main())
```

### Pattern 7: Webhook Verification (Source: official)

Verify and parse inbound OpenAI webhook payloads to prevent spoofed events.

```typescript
import { headers } from 'next/headers';
import OpenAI from 'openai';

const client = new OpenAI();
const webhookSecret = process.env['OPENAI_WEBHOOK_SECRET']!;

export async function POST(req: Request) {
  const body = await req.text(); // raw string — do NOT parse first
  const headersList = headers();

  let event;
  try {
    event = client.webhooks.unwrap(body, headersList, webhookSecret);
  } catch (err) {
    return new Response('Invalid webhook signature', { status: 400 });
  }

  console.log('Verified event type:', event.type);
  return new Response('OK', { status: 200 });
}
```

### Pattern 8: Error Handling and Retries (Source: community)

Context-length and rate-limit errors are the two most common production failures. Handle both defensively.
Source: community / Tested: SharpSkill

```python
import time
from openai import OpenAI, APIError, RateLimitError, BadRequestError

client = OpenAI()

def safe_complete(messages: list, model: str = "gpt-4o", max_retries: int = 3) -> str:
    """
    Handles the two most common OpenAI failure modes:
      - 429 RateLimitError: exponential back-off
      - 400 context_length_exceeded: trim oldest non-system messages
    # Source: community / # Tested: SharpSkill
    """
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
            )
            return resp.choices[0].message.content

        except RateLimitError as e:
            wait = 2 ** attempt
            print(f"Rate limited. Retrying in {wait}s… ({e})")
            time.sleep(wait)

        except BadRequestError as e:
            if "context_length_exceeded" in str(e) or "maximum context length" in str(e):
                # Drop the oldest non-system message and retry
                non_system = [i for i, m in enumerate(messages) if m["role"] != "system"]
                if non_system:
                    print(f"Context too long. Dropping message at index {non_system[0]}.")
                    messages.pop(non_system[0])
                else:
                    raise  # Cannot trim further
            else:
                raise

        except APIError as e:
            print(f"API error: {e}")
            raise

    raise RuntimeError("Max retries exceeded.")
```

## Production Notes

1. **Context length overflow crashes agents** — When using GPT-3.5 (4 097-token limit) or even GPT-4 with long conversation history, accumulated messages silently exceed the context window, causing `InvalidRequestError: maximum context length`. Implement a sliding-window or summarisation strategy. Trim from the oldest non-system message first. *Source: GitHub Issues (AutoGPT #3 and #5 above)*

2. **Invalid JSON responses from function calling** — The model occasionally returns malformed JSON in function-call arguments. Always wrap JSON parsing in try/except and retry with an explicit prompt: `"Respond ONLY with valid JSON, no prose."` Adding `response_format: { type: "json_object" }` (where supported) is the most reliable fix. *Source: GitHub Issues (community bug: Invalid JSON)*

3. **Local memory / file persistence warnings** — When file-based memory (e.g., `auto-gpt.json`) does not exist on first run, agents print warnings and silently skip persistence. Always pre-create the file or handle the `FileNotFoundError` gracefully at startup. *Source: GitHub Issues (AutoGPT memory bugs)*

4. **Streaming + async generators must be fully consumed** — Abandoning a streaming iterator without iterating all chunks leaves the HTTP connection open, causing resource leaks and eventual `TimeoutError`. Always wrap streams in `try/finally` to close them, or use the SDK's built-in context manager (`with client.responses.stream(...) as stream`). *Source: community / Tested: SharpSkill*

5. **API key stored in source control** — The SDK reads `OPENAI_API_KEY` from the environment by default. Never hard-code the key. Use `python-dotenv` (Python) or `dotenv` (Node) and add `.env` to `.gitignore`. Rotate immediately if exposed. *Source: official docs warning*

## Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `BadRequestError: maximum context length exceeded` | Total tokens (prompt + history + completion) exceed model limit (e.g., 4 097 for gpt-3.5-turbo) | Trim oldest messages, summarise history, or switch to a higher-context model (gpt-4o = 128 k) |
| `RateLimitError: 429 Too Many Requests` | Exceeded requests-per-minute or tokens-per-minute quota | Implement exponential back-off; request quota increase in OpenAI dashboard |
| `AuthenticationError: No API key provided` | `OPENAI_API_KEY` env var not set or key is invalid/revoked | Set env var; regenerate key at platform.openai.com; verify `.env` is loaded |
| Malformed / incomplete JSON in function-call arguments | Model occasionally produces truncated JSON under high load or near token limit | Increase `max_tokens`, add `response_format: { type: "json_object" }`, validate and retry |
| Webhook returns 400 / signature mismatch | Webhook body was parsed (JSON.parse) before verification, mutating raw bytes | Pass raw string body directly to `client.webhooks.unwrap()` — never parse first |
| `ConnectionError` or `TimeoutError` during file upload | Large file uploads timing out on slow connections | Use `fs.createReadStream()` (not `Buffer.from`); increase `httpAgent` timeout in client config |

## Pre-Deploy Checklist

- [ ] `OPENAI_API_KEY` set via environment variable, not hard-coded; `.env` in `.gitignore`
- [ ] Model name matches a model your account has access to (check platform.openai.com/account/limits)
- [ ] `max_tokens` explicitly set to prevent runaway costs on unexpectedly long outputs
- [ ] Context-length guard implemented: trim or summarise conversation history before each request
- [ ] Rate-limit retry logic with exponential back-off in place for all API calls
- [ ] Webhook signature verified with `client.webhooks.unwrap()` using raw (unparsed) request body
- [ ] Streaming iterators always fully consumed or closed in `try/finally` / context managers

## Troubleshooting

**Error: `BadRequestError: This model's maximum context length is 4097 tokens`**
Cause: The total tokens across all messages (system + history + new user message) exceed the model's limit.
Fix: (1) Switch to `gpt-4o` (128 k context). (2) Implement sliding-window pruning — drop or summarise the oldest non-system messages. (3) Count tokens before the request using `tiktoken` (Python) or `js-tiktoken` (Node).

**Error: `AuthenticationError: Incorrect API key provided`**
Cause: The key is wrong, revoked, or the env var is not loaded into the current process.
Fix: Verify with `echo $OPENAI_API_KEY`; ensure `dotenv.config()` / `load_dotenv()` is called before the client is instantiated.

**Error: `RateLimitError: Rate limit reached for gpt-4`**
Cause: Requests-per-minute (RPM) or tokens-per-minute (TPM) quota exhausted.
Fix: Add exponential back-off (start at 1 s, cap at 60 s); use `gpt-4o-mini` for lower-priority tasks; request a quota increase via the OpenAI dashboard.

**Warning: `The file 'auto-gpt.json' does not exist. Local memory would not be saved.`**
Cause: Agent-based frameworks (AutoGPT, LangChain) expect a pre-existing local memory file.
Fix: Create the file before first run (`echo '{}' > auto-gpt.json`) or catch `FileNot