"""
PWS Content Template - Manual Content Ingestion

INSTRUCTIONS:
1. Export your Google Drive content to text/markdown
2. Paste content into the appropriate sections below
3. Run: python scripts/pws_content_template.py --upsert

This template provides structured content entry for optimal RAG retrieval.
Each content block should follow the metadata schema for best results.

METADATA SCHEMA:
================
- id: Unique identifier (auto-generated or manual)
- content: The actual text content (will be embedded)
- title: Human-readable title for display
- category: One of the categories below
- type: Specific type within category
- source: Original source (filename, URL, etc.)
- tags: List of tags for filtering
- problem_type: un-defined | ill-defined | well-defined | all
- week: Course week number (1-10) if applicable
- framework_name: Framework identifier if applicable

CATEGORIES:
===========
- Framework: Problem-solving frameworks (JTBD, Minto, etc.)
- Course Module: PWS course content (Week 1-10)
- Book: Book summaries and key concepts
- Case Study: Real-world examples and applications
- Core Methodology: PWS core principles
- Validation Tool: Assessment and validation tools
- Agent Methodology: Larry, Devil's Advocate behaviors
- Exercise: Worksheets and exercises
- Template: Output templates
- Reference: General reference material

CHUNKING GUIDELINES:
===================
- Ideal chunk size: 500-1500 characters
- Each chunk should be self-contained (makes sense on its own)
- Include context in each chunk (don't assume prior chunks were read)
- For long content, split by topic/section, not arbitrarily
"""

import os
import asyncio
import httpx
from typing import List, Dict, Any

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_HOST = "neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io"
NAMESPACE = "pws-materials"


# ============================================================================
# CONTENT BLOCKS - PASTE YOUR CONTENT HERE
# ============================================================================

CONTENT_BLOCKS: List[Dict[str, Any]] = [

    # -------------------------------------------------------------------------
    # EXAMPLE BLOCK - Replace with your actual content
    # -------------------------------------------------------------------------
    # {
    #     "id": "framework-your-framework-1",  # Unique ID
    #     "title": "Your Framework Name",
    #     "category": "Framework",
    #     "type": "framework",
    #     "source": "google-drive-folder-name",
    #     "tags": ["framework", "strategy", "innovation"],
    #     "problem_type": "ill-defined",  # or "un-defined", "well-defined", "all"
    #     "week": None,  # Set to "1", "2", etc. for course materials
    #     "framework_name": "your-framework",  # Optional identifier
    #     "content": """
    #     Your framework content goes here...
    #
    #     Can be multiple paragraphs. The content should be
    #     self-contained and make sense on its own.
    #
    #     Include key concepts, steps, examples, etc.
    #     """,
    # },

    # -------------------------------------------------------------------------
    # FOLDER 1: [Add folder name here]
    # -------------------------------------------------------------------------


    # -------------------------------------------------------------------------
    # FOLDER 2: [Add folder name here]
    # -------------------------------------------------------------------------


    # -------------------------------------------------------------------------
    # FOLDER 3: [Add folder name here]
    # -------------------------------------------------------------------------


    # -------------------------------------------------------------------------
    # FOLDER 4: [Add folder name here]
    # -------------------------------------------------------------------------


]


# ============================================================================
# COURSE MODULE TEMPLATE
# ============================================================================

COURSE_MODULES: List[Dict[str, Any]] = [
    # Week X Template - Copy and modify for each week
    # {
    #     "id": "pws-module-X",
    #     "title": "Week X: [Module Title]",
    #     "category": "Course Module",
    #     "type": "course-module",
    #     "source": "pws-course",
    #     "tags": ["pws", "course", "week-X"],
    #     "problem_type": "all",  # or specific type
    #     "week": "X",
    #     "content": """
    #     [Module overview and key concepts]
    #
    #     DELIVERABLES:
    #     - Deliverable 1
    #     - Deliverable 2
    #     - Deliverable 3
    #
    #     KEY FRAMEWORKS:
    #     - Framework 1
    #     - Framework 2
    #
    #     LEARNING OUTCOMES:
    #     - Outcome 1
    #     - Outcome 2
    #     """,
    # },
]


# ============================================================================
# FRAMEWORK TEMPLATE
# ============================================================================

FRAMEWORKS: List[Dict[str, Any]] = [
    # Framework Template - Copy and modify for each framework
    # {
    #     "id": "framework-[name]-1",
    #     "title": "[Framework Name]",
    #     "category": "Framework",
    #     "type": "framework",
    #     "source": "pws-frameworks",
    #     "tags": ["framework", "[category]"],
    #     "problem_type": "[type]",
    #     "framework_name": "[identifier]",
    #     "content": """
    #     [Framework Name] - [One-line description]
    #
    #     PURPOSE:
    #     [What problem does this framework solve?]
    #
    #     WHEN TO USE:
    #     - Situation 1
    #     - Situation 2
    #
    #     HOW IT WORKS:
    #     1. Step 1
    #     2. Step 2
    #     3. Step 3
    #
    #     KEY COMPONENTS:
    #     - Component 1: [description]
    #     - Component 2: [description]
    #
    #     EXAMPLE:
    #     [Brief example of framework in action]
    #
    #     OUTPUT:
    #     [What deliverable does this framework produce?]
    #     """,
    # },
]


# ============================================================================
# BOOK SUMMARIES TEMPLATE
# ============================================================================

BOOK_SUMMARIES: List[Dict[str, Any]] = [
    # Book Summary Template
    # {
    #     "id": "book-[name]-1",
    #     "title": "[Book Title] - Summary",
    #     "category": "Book",
    #     "type": "book-summary",
    #     "source": "[author-name]",
    #     "tags": ["book", "[topic]"],
    #     "problem_type": "all",
    #     "content": """
    #     [Book Title] by [Author]
    #
    #     CORE THESIS:
    #     [Main argument of the book]
    #
    #     KEY CONCEPTS:
    #     1. [Concept 1]: [Explanation]
    #     2. [Concept 2]: [Explanation]
    #     3. [Concept 3]: [Explanation]
    #
    #     APPLICATIONS TO PWS:
    #     - [How this applies to problem-solving]
    #     - [How this applies to innovation]
    #
    #     KEY QUOTES:
    #     - "[Quote 1]"
    #     - "[Quote 2]"
    #
    #     RECOMMENDED FOR:
    #     [When/who should reference this]
    #     """,
    # },
]


# ============================================================================
# UPSERT FUNCTIONS
# ============================================================================

def prepare_record(block: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a content block for Pinecone upsert"""
    record = {
        "_id": block["id"],
        "content": block["content"].strip(),
        "title": block["title"],
        "category": block["category"],
        "type": block["type"],
        "source": block["source"],
        "tags": ", ".join(block.get("tags", [])),
    }

    # Add optional fields
    if block.get("problem_type"):
        record["problem_type"] = block["problem_type"]
    if block.get("week"):
        record["week"] = block["week"]
    if block.get("framework_name"):
        record["framework_name"] = block["framework_name"]

    return record


async def upsert_records(records: List[Dict[str, Any]], namespace: str = NAMESPACE):
    """Upsert records to Pinecone"""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not set")

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {
            "Api-Key": PINECONE_API_KEY,
            "Content-Type": "application/json",
        }

        url = f"https://{INDEX_HOST}/records/namespaces/{namespace}/upsert"

        # Batch upsert (max 100 records per batch)
        batch_size = 50
        total = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            response = await client.post(
                url,
                headers=headers,
                json={"records": batch},
            )
            response.raise_for_status()
            total += len(batch)
            print(f"  Upserted batch: {len(batch)} records (total: {total})")

        return total


async def main(dry_run: bool = True):
    """Main function"""
    # Combine all content
    all_blocks = (
        CONTENT_BLOCKS +
        COURSE_MODULES +
        FRAMEWORKS +
        BOOK_SUMMARIES
    )

    # Filter out empty blocks
    all_blocks = [b for b in all_blocks if b.get("content", "").strip()]

    if not all_blocks:
        print("No content blocks defined. Add content to the templates above.")
        return

    print(f"Found {len(all_blocks)} content blocks")

    # Prepare records
    records = [prepare_record(b) for b in all_blocks]

    # Show summary
    categories = {}
    for r in records:
        cat = r["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    if dry_run:
        print("\n[DRY RUN] Would upsert the following records:")
        for r in records[:5]:  # Show first 5
            print(f"  - {r['_id']}: {r['title']}")
        if len(records) > 5:
            print(f"  ... and {len(records) - 5} more")
        print("\nRun with --upsert to actually upload to Pinecone")
    else:
        print(f"\nUpserting to Pinecone namespace: {NAMESPACE}")
        count = await upsert_records(records)
        print(f"\nSuccessfully upserted {count} records")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PWS Content Ingestion")
    parser.add_argument("--upsert", action="store_true", help="Actually upsert to Pinecone")
    args = parser.parse_args()

    asyncio.run(main(dry_run=not args.upsert))
