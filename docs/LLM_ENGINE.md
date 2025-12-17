# Mindrian LLM Engine Configuration

> Multi-provider LLM configuration for Anthropic Claude + Google Gemini

---

## Overview

Mindrian uses a **multi-provider LLM architecture**:

| Provider | Model | Use Case |
|----------|-------|----------|
| **Anthropic Claude** | claude-sonnet-4-20250514 | Complex reasoning, clarification, synthesis |
| **Google Gemini** | gemini-2.0-flash-exp | Fast tasks, classification, summarization |

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LLM ENGINE                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐              ┌──────────────────┐             │
│  │   Anthropic      │              │     Google       │             │
│  │   Claude         │              │     Gemini       │             │
│  ├──────────────────┤              ├──────────────────┤             │
│  │ • Complex reason │              │ • Classification │             │
│  │ • Clarification  │              │ • Summarization  │             │
│  │ • Synthesis      │              │ • Extraction     │             │
│  │ • Framework ops  │              │ • Fast queries   │             │
│  └────────┬─────────┘              └────────┬─────────┘             │
│           │                                  │                       │
│           └────────────┬────────────────────┘                       │
│                        │                                             │
│                        ▼                                             │
│              ┌─────────────────┐                                    │
│              │  Task Router    │                                    │
│              │  ─────────────  │                                    │
│              │  get_model_for_ │                                    │
│              │  task(task_type)│                                    │
│              └─────────────────┘                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

```bash
# ═══════════════════════════════════════════════════════════════════════════
# LLM PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════

# Anthropic Claude (Primary - complex reasoning)
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_DEFAULT_MODEL=claude-sonnet-4-20250514

# Google Gemini (Secondary - speed/cost optimization)
GOOGLE_API_KEY=AIza...
GOOGLE_DEFAULT_MODEL=gemini-2.0-flash-exp

# Default provider when task type is unknown
DEFAULT_LLM_PROVIDER=anthropic  # or "google"

# ═══════════════════════════════════════════════════════════════════════════
# EMBEDDINGS (for Supabase pgvector)
# ═══════════════════════════════════════════════════════════════════════════

EMBEDDING_PROVIDER=google
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSIONS=768
```

---

## Task-Based Model Routing

The LLM engine automatically routes tasks to the optimal provider:

```python
# Default routing configuration
model_routing = {
    # Complex reasoning tasks → Anthropic Claude
    "complex_reasoning": ("anthropic", "claude-sonnet-4-20250514"),
    "clarification": ("anthropic", "claude-sonnet-4-20250514"),
    "synthesis": ("anthropic", "claude-sonnet-4-20250514"),

    # Fast/simple tasks → Google Gemini
    "classification": ("google", "gemini-2.0-flash-exp"),
    "summarization": ("google", "gemini-2.0-flash-exp"),
    "extraction": ("google", "gemini-2.0-flash-exp"),
}
```

### Agent Type to Task Mapping

| Agent Type | Task Type | Provider |
|------------|-----------|----------|
| ROLE (Larry, Devil) | clarification | Anthropic |
| OPERATOR (Minto, PWS) | complex_reasoning | Anthropic |
| COLLABORATIVE (De Bono) | synthesis | Anthropic |
| Router | classification | Google |
| Summarizer | summarization | Google |

---

## Usage in Code

### 1. Get Settings

```python
from mindrian.config import settings

# Access LLM config
print(settings.llm.anthropic_api_key)
print(settings.llm.google_default_model)
```

### 2. Get Model for Task

```python
from mindrian.config import settings

# Route to optimal provider
provider, model = settings.llm.get_model_for_task("complex_reasoning")
# Returns: ("anthropic", "claude-sonnet-4-20250514")

provider, model = settings.llm.get_model_for_task("classification")
# Returns: ("google", "gemini-2.0-flash-exp")

# Unknown task uses default provider
provider, model = settings.llm.get_model_for_task("unknown_task")
# Returns based on DEFAULT_LLM_PROVIDER
```

### 3. Get LLM Clients

```python
from mindrian.config import get_anthropic_client, get_google_client

# Anthropic client
anthropic = get_anthropic_client()
response = anthropic.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello"}]
)

# Google client
genai = get_google_client()
model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("Hello")
```

### 4. Embeddings

```python
from mindrian.config import settings, get_embedding_model

# Get embedding function
embed = get_embedding_model()

# Generate embedding (768 dimensions with Google)
embedding = embed(
    model=settings.embedding.model,
    content="Text to embed",
    task_type="retrieval_document"
)
```

---

## Integration with Agno Agents

### Agent Spec Configuration

```yaml
# Agent spec defining model provider
model:
  provider: anthropic          # or "google"
  id: claude-sonnet-4-20250514  # or gemini-2.0-flash-exp

  # Extended thinking (Claude only)
  thinking:
    enabled: true
    budget_tokens: 8000
```

### Creating Agents with Agno

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from mindrian.config import settings

# Create agent with Claude
larry_agent = Agent(
    model=Claude(
        id=settings.llm.anthropic_default_model,
        api_key=settings.llm.anthropic_api_key
    ),
    instructions="You are Larry, the clarifier...",
)

# Create agent with Gemini (for fast tasks)
router_agent = Agent(
    model=Gemini(
        id=settings.llm.google_default_model,
        api_key=settings.llm.google_api_key
    ),
    instructions="Classify the problem type...",
)
```

### Dynamic Model Selection

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from mindrian.config import settings

def create_agent_for_task(task_type: str, instructions: str) -> Agent:
    """Create agent with optimal model for task type"""
    provider, model_id = settings.llm.get_model_for_task(task_type)

    if provider == "anthropic":
        model = Claude(
            id=model_id,
            api_key=settings.llm.anthropic_api_key
        )
    else:
        model = Gemini(
            id=model_id,
            api_key=settings.llm.google_api_key
        )

    return Agent(model=model, instructions=instructions)

# Usage
larry = create_agent_for_task("clarification", "You are Larry...")
router = create_agent_for_task("classification", "Classify problems...")
```

---

## Extended Thinking (Claude)

For complex reasoning tasks, enable extended thinking:

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

agent = Agent(
    model=Claude(
        id="claude-sonnet-4-20250514",
        api_key=settings.llm.anthropic_api_key,
        # Extended thinking configuration
        thinking={
            "type": "enabled",
            "budget_tokens": 10000
        }
    ),
    instructions="Deep analysis agent..."
)
```

### Thinking Budget by Agent Type

| Agent Type | Thinking Budget |
|------------|-----------------|
| ROLE | 2,000 tokens |
| OPERATOR | 8,000 tokens |
| COLLABORATIVE | 15,000 tokens |
| PIPELINE | 10,000 tokens |

---

## Model Specifications

### Anthropic Claude

| Model | Context | Best For |
|-------|---------|----------|
| claude-sonnet-4-20250514 | 200K | Complex reasoning, analysis |
| claude-opus-4 | 200K | Deepest reasoning (higher cost) |
| claude-haiku-3-5 | 200K | Fast, simple tasks |

### Google Gemini

| Model | Context | Best For |
|-------|---------|----------|
| gemini-2.0-flash-exp | 1M | Fast generation, multimodal |
| gemini-2.0-pro | 2M | Complex tasks, long context |

---

## Cost Optimization

The multi-provider approach optimizes costs:

```
┌────────────────────────────────────────────────────────────────┐
│                    COST OPTIMIZATION                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  High-Value Tasks (Claude)          Low-Cost Tasks (Gemini)    │
│  ═════════════════════════          ══════════════════════     │
│                                                                 │
│  • Problem clarification            • Intent classification    │
│  • Framework application            • Summary generation       │
│  • Insight synthesis                • Entity extraction        │
│  • Quality validation               • Simple routing           │
│                                                                 │
│  ~$15/1M tokens                     ~$0.075/1M tokens          │
│                                                                 │
│  Result: 80% cost reduction on simple tasks                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### API Key Issues

```python
# Verify keys are loaded
from mindrian.config import settings

assert settings.llm.anthropic_api_key, "Missing ANTHROPIC_API_KEY"
assert settings.llm.google_api_key, "Missing GOOGLE_API_KEY"
```

### Model Not Found

```python
# Check available models
from anthropic import Anthropic
client = Anthropic()
# Claude models are pre-defined, check docs for latest

import google.generativeai as genai
for model in genai.list_models():
    print(model.name)
```

### Embedding Dimension Mismatch

Ensure your Supabase vector column matches:

```sql
-- Google text-embedding-004 = 768 dimensions
ALTER TABLE conversations
ALTER COLUMN embedding TYPE vector(768);
```

---

*Mindrian LLM Engine v1.0*
