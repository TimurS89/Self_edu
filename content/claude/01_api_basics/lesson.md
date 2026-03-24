# Claude API Basics: Your First API Call

## What is the Claude API?

The Claude API lets you integrate Claude's intelligence directly into your code. Instead of chatting in a browser, you send requests programmatically and get structured responses back.

## Setting Up

Install the Anthropic Python SDK:

```bash
pip install anthropic
```

Set your API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Your First API Call

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(message.content[0].text)
# "The capital of France is Paris."
```

## Key Concepts

### Messages API

The Messages API is Claude's primary interface. Every request needs:
- **model**: Which Claude model to use
- **max_tokens**: Maximum response length
- **messages**: A list of conversation messages

### Message Roles

- `"user"`: Your message (the human)
- `"assistant"`: Claude's response (can be provided for few-shot examples)

### System Prompts

Set Claude's behavior with a system prompt:

```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="You are a helpful Japanese tutor. Always include romaji.",
    messages=[
        {"role": "user", "content": "How do I say 'good morning'?"}
    ]
)
```

## Available Models

| Model | Best For |
|-------|----------|
| Claude Opus 4 | Most capable, complex reasoning |
| Claude Sonnet 4 | Best balance of speed and capability |
| Claude Haiku 3.5 | Fastest, cheapest, simple tasks |

## Response Structure

```python
# The response object contains:
message.content        # List of content blocks
message.content[0].text  # The actual text response
message.model          # Model used
message.usage          # Token counts (input + output)
message.stop_reason    # Why Claude stopped ("end_turn", "max_tokens")
```

## Key Takeaways

1. Use `anthropic.Anthropic()` to create a client
2. `client.messages.create()` is the main method
3. Messages are a list of `{"role": ..., "content": ...}` dicts
4. System prompts control Claude's behavior
5. Always check `message.usage` to understand token costs
