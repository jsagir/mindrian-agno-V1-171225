# PWS Brain Ingestion Guide

## Overview

This system ingests PWS (Personal Wisdom System) materials into Pinecone for RAG-powered conversations with Larry.

## Quick Start

### Option 1: Export Google Drive → Local Directory → Ingest

```bash
# 1. Export Google Drive folders to local directory
#    (Download as .md, .txt, or .json files)

# 2. Process the directory
python scripts/pws_brain_ingestion.py --input-dir /path/to/materials --output review.json

# 3. Review the chunks
cat review.json | jq '.[] | .title'

# 4. Upsert to Pinecone
python scripts/pws_brain_ingestion.py --input-dir /path/to/materials --upsert
```

### Option 2: Manual Content Entry (Recommended for curated content)

```bash
# 1. Edit the template file
#    Open: scripts/pws_content_template.py

# 2. Add content blocks following the templates

# 3. Dry run to check
python scripts/pws_content_template.py

# 4. Upsert to Pinecone
python scripts/pws_content_template.py --upsert
```

## Metadata Schema

### Required Fields
| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique identifier | `framework-jtbd-1` |
| `content` | Text content (embedded) | The actual framework text |
| `title` | Display title | "Jobs to Be Done Framework" |
| `category` | High-level category | "Framework" |
| `type` | Specific type | "framework" |
| `source` | Origin reference | "pws-course-materials" |
| `tags` | Comma-separated tags | "framework, jtbd, customer" |

### Optional Fields
| Field | Description | Example |
|-------|-------------|---------|
| `problem_type` | Problem classification | "ill-defined" |
| `week` | Course week number | "3" |
| `framework_name` | Framework identifier | "jtbd" |
| `chunk_index` | Position in document | "0" |
| `total_chunks` | Total parts | "3" |

### Categories
- `Framework` - Problem-solving frameworks
- `Course Module` - PWS course content (Week 1-10)
- `Book` - Book summaries
- `Case Study` - Real-world examples
- `Core Methodology` - PWS core principles
- `Validation Tool` - Assessment tools
- `Agent Methodology` - Larry/Devil behaviors
- `Exercise` - Worksheets
- `Template` - Output templates
- `Reference` - General reference

### Problem Types
- `un-defined` - Future-focused (5-15 year horizon)
- `ill-defined` - Opportunity-focused (1-5 year horizon)
- `well-defined` - Solution-focused (0-12 month horizon)
- `all` - Applies to all types

## Chunking Guidelines

### Ideal Chunk Characteristics
1. **Self-contained**: Makes sense without reading other chunks
2. **Focused**: One topic/concept per chunk
3. **Right-sized**: 500-1500 characters (ideal for embedding)
4. **Context-rich**: Includes enough context to understand

### Bad Chunking (Avoid)
```
❌ "See above for the framework steps..."
❌ "As mentioned earlier..."
❌ Arbitrary splits mid-paragraph
❌ Chunks that are too short (<200 chars)
❌ Chunks that are too long (>2000 chars)
```

### Good Chunking (Do This)
```
✅ Each chunk explains a complete concept
✅ Key terms are defined in the chunk
✅ Examples are included where relevant
✅ The title accurately describes content
```

## Content Templates

### Framework Template
```python
{
    "id": "framework-[name]-1",
    "title": "[Framework Name]",
    "category": "Framework",
    "type": "framework",
    "source": "pws-materials",
    "tags": ["framework", "[topic]"],
    "problem_type": "[type]",
    "framework_name": "[identifier]",
    "content": """
    [Framework Name] - [One-line description]

    PURPOSE:
    [What problem does this framework solve?]

    WHEN TO USE:
    - Situation 1
    - Situation 2

    HOW IT WORKS:
    1. Step 1
    2. Step 2
    3. Step 3

    OUTPUT:
    [What deliverable does this framework produce?]
    """,
}
```

### Course Module Template
```python
{
    "id": "pws-module-[week]",
    "title": "Week [X]: [Module Title]",
    "category": "Course Module",
    "type": "course-module",
    "source": "pws-course",
    "tags": ["pws", "course", "week-[X]"],
    "problem_type": "[type]",
    "week": "[X]",
    "content": """
    [Module overview]

    DELIVERABLES:
    - Deliverable 1
    - Deliverable 2

    KEY FRAMEWORKS:
    - Framework 1
    - Framework 2
    """,
}
```

## Pinecone Index Info

- **Index**: `neo4j-knowledge-base`
- **Host**: `neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io`
- **Namespace**: `pws-materials`
- **Embedding Model**: `multilingual-e5-large` (integrated inference)
- **Dimensions**: 1024

## Testing After Ingestion

```bash
# Search for content
curl -X POST "https://neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io/records/namespaces/pws-materials/query" \
  -H "Api-Key: $PINECONE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"inputs": {"text": "Your search query"}, "top_k": 5}
  }'
```

Or via the Mindrian API:
```bash
curl -X POST "http://localhost:8000/ai/pws-brain/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Your search query", "top_k": 5}'
```
