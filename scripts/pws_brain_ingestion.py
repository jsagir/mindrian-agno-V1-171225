"""
PWS Brain Ingestion Pipeline

This script handles chunking and upserting PWS materials to Pinecone
for optimal RAG performance in Mindrian conversations.

USAGE:
1. Export Google Drive folders to local directory
2. Run: python scripts/pws_brain_ingestion.py --input-dir /path/to/materials

CHUNKING STRATEGY:
- Semantic chunking (not fixed-size) for better retrieval
- Overlap between chunks for context preservation
- Metadata enrichment for filtering and ranking

METADATA SCHEMA:
- category: High-level category (Framework, Course Module, Book, etc.)
- type: Specific type within category
- title: Human-readable title
- source: Original file/document name
- week: Course week number (if applicable)
- framework_name: Framework identifier (if applicable)
- problem_type: un-defined | ill-defined | well-defined
- tags: List of relevant tags for filtering
- chunk_index: Position in original document
- total_chunks: Total chunks from this document
"""

import os
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_HOST = "neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io"
INDEX_NAME = "neo4j-knowledge-base"
NAMESPACE = "pws-materials"


class Category(str, Enum):
    """Content categories for filtering"""
    FRAMEWORK = "Framework"
    COURSE_MODULE = "Course Module"
    BOOK = "Book"
    CASE_STUDY = "Case Study"
    METHODOLOGY = "Core Methodology"
    TOOL = "Validation Tool"
    AGENT = "Agent Methodology"
    EXERCISE = "Exercise"
    TEMPLATE = "Template"
    REFERENCE = "Reference"


class ProblemType(str, Enum):
    """Problem classification types"""
    UNDEFINED = "un-defined"
    ILL_DEFINED = "ill-defined"
    WELL_DEFINED = "well-defined"
    ALL = "all"  # Applies to all types


@dataclass
class PWSChunk:
    """A chunk of PWS content ready for upsert"""
    id: str
    content: str
    title: str
    category: str
    type: str
    source: str
    tags: List[str]
    problem_type: Optional[str] = None
    week: Optional[str] = None
    framework_name: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 1

    def to_pinecone_record(self) -> Dict[str, Any]:
        """Convert to Pinecone record format"""
        record = {
            "_id": self.id,
            "content": self.content,  # This is the field mapped for embedding
            "title": self.title,
            "category": self.category,
            "type": self.type,
            "source": self.source,
            "tags": ", ".join(self.tags),  # Pinecone prefers flat strings
        }

        # Add optional fields
        if self.problem_type:
            record["problem_type"] = self.problem_type
        if self.week:
            record["week"] = self.week
        if self.framework_name:
            record["framework_name"] = self.framework_name
        if self.total_chunks > 1:
            record["chunk_index"] = str(self.chunk_index)
            record["total_chunks"] = str(self.total_chunks)

        return record


def generate_chunk_id(content: str, source: str, index: int) -> str:
    """Generate deterministic chunk ID"""
    hash_input = f"{source}:{index}:{content[:100]}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might cause issues
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return text.strip()


def semantic_chunk(
    text: str,
    max_chunk_size: int = 1500,
    min_chunk_size: int = 200,
    overlap: int = 100,
) -> List[str]:
    """
    Semantic chunking - splits on natural boundaries.

    Priority:
    1. Double newlines (paragraphs)
    2. Single newlines
    3. Sentences (. ! ?)
    4. Hard split at max_chunk_size
    """
    text = clean_text(text)

    if len(text) <= max_chunk_size:
        return [text] if len(text) >= min_chunk_size else []

    chunks = []
    current_chunk = ""

    # Split on paragraphs first
    paragraphs = re.split(r'\n\n+', text)

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If paragraph fits in current chunk
        if len(current_chunk) + len(para) + 2 <= max_chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            # Save current chunk if it meets minimum
            if len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk = overlap_text + ("\n\n" if overlap_text else "") + para
            else:
                # Paragraph is too long, split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                        current_chunk += (" " if current_chunk else "") + sentence
                    else:
                        if len(current_chunk) >= min_chunk_size:
                            chunks.append(current_chunk)
                        current_chunk = sentence

    # Don't forget the last chunk
    if len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk)

    return chunks


def detect_category(filename: str, content: str) -> Category:
    """Detect content category from filename and content"""
    filename_lower = filename.lower()
    content_lower = content[:500].lower()

    if "framework" in filename_lower or "framework" in content_lower:
        return Category.FRAMEWORK
    elif "week" in filename_lower or "module" in filename_lower:
        return Category.COURSE_MODULE
    elif "book" in filename_lower or "summary" in filename_lower:
        return Category.BOOK
    elif "case" in filename_lower or "example" in filename_lower:
        return Category.CASE_STUDY
    elif "exercise" in filename_lower or "worksheet" in filename_lower:
        return Category.EXERCISE
    elif "template" in filename_lower:
        return Category.TEMPLATE
    elif "larry" in filename_lower or "devil" in filename_lower:
        return Category.AGENT
    elif "pws" in filename_lower or "validation" in filename_lower:
        return Category.METHODOLOGY
    else:
        return Category.REFERENCE


def detect_problem_type(content: str) -> Optional[str]:
    """Detect which problem type this content relates to"""
    content_lower = content.lower()

    undefined_keywords = ["future", "scenario", "trend", "10 year", "absurd", "emerging"]
    illdefined_keywords = ["jtbd", "jobs to be done", "opportunity", "customer need", "unmet"]
    welldefined_keywords = ["validation", "issue tree", "hypothesis", "falsify", "test"]

    scores = {
        ProblemType.UNDEFINED: sum(1 for k in undefined_keywords if k in content_lower),
        ProblemType.ILL_DEFINED: sum(1 for k in illdefined_keywords if k in content_lower),
        ProblemType.WELL_DEFINED: sum(1 for k in welldefined_keywords if k in content_lower),
    }

    max_score = max(scores.values())
    if max_score == 0:
        return ProblemType.ALL.value

    return max(scores, key=scores.get).value


def extract_week_number(filename: str, content: str) -> Optional[str]:
    """Extract week number from course materials"""
    # Try filename first
    match = re.search(r'week\s*(\d+)', filename, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try content
    match = re.search(r'week\s*(\d+)', content[:200], re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extract_tags(content: str, category: Category) -> List[str]:
    """Extract relevant tags from content"""
    tags = [category.value.lower().replace(" ", "-")]

    # Framework-specific tags
    framework_patterns = [
        (r"minto pyramid", "minto"),
        (r"scqa", "scqa"),
        (r"jobs.to.be.done|jtbd", "jtbd"),
        (r"cynefin", "cynefin"),
        (r"de bono|six hats", "debono"),
        (r"devil.?s advocate", "devils-advocate"),
        (r"scenario analysis", "scenario"),
        (r"trending.to.absurd", "trending-absurd"),
        (r"issue tree", "issue-tree"),
        (r"5 whys|five whys", "5-whys"),
        (r"golden circle", "golden-circle"),
        (r"business model canvas", "bmc"),
        (r"value proposition", "value-prop"),
        (r"lean canvas", "lean-canvas"),
        (r"problem.worth.solving|pws", "pws"),
    ]

    content_lower = content.lower()
    for pattern, tag in framework_patterns:
        if re.search(pattern, content_lower):
            tags.append(tag)

    # Problem type tags
    if "innovation" in content_lower:
        tags.append("innovation")
    if "startup" in content_lower:
        tags.append("startup")
    if "strategy" in content_lower:
        tags.append("strategy")
    if "customer" in content_lower:
        tags.append("customer")
    if "market" in content_lower:
        tags.append("market")

    return list(set(tags))  # Deduplicate


def process_file(filepath: Path) -> List[PWSChunk]:
    """Process a single file into chunks"""
    try:
        # Read file content
        if filepath.suffix.lower() == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    content = "\n\n".join(str(item) for item in data)
                elif isinstance(data, dict):
                    content = json.dumps(data, indent=2)
                else:
                    content = str(data)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

        if not content or len(content.strip()) < 50:
            print(f"  Skipping {filepath.name} - too short")
            return []

        # Detect metadata
        category = detect_category(filepath.name, content)
        problem_type = detect_problem_type(content)
        week = extract_week_number(filepath.name, content)
        tags = extract_tags(content, category)

        # Extract title from filename
        title = filepath.stem.replace("_", " ").replace("-", " ").title()

        # Chunk the content
        text_chunks = semantic_chunk(content)

        if not text_chunks:
            print(f"  Skipping {filepath.name} - no valid chunks")
            return []

        # Create PWSChunk objects
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = generate_chunk_id(chunk_text, filepath.name, i)

            chunk = PWSChunk(
                id=f"{category.value.lower().replace(' ', '-')}-{chunk_id}",
                content=chunk_text,
                title=f"{title}" + (f" (Part {i+1})" if len(text_chunks) > 1 else ""),
                category=category.value,
                type=filepath.suffix.lstrip('.'),
                source=filepath.name,
                tags=tags,
                problem_type=problem_type,
                week=week,
                chunk_index=i,
                total_chunks=len(text_chunks),
            )
            chunks.append(chunk)

        return chunks

    except Exception as e:
        print(f"  Error processing {filepath.name}: {e}")
        return []


def process_directory(input_dir: Path) -> List[PWSChunk]:
    """Process all files in a directory"""
    all_chunks = []

    # Supported file extensions
    extensions = {'.txt', '.md', '.json', '.csv'}

    for filepath in input_dir.rglob('*'):
        if filepath.is_file() and filepath.suffix.lower() in extensions:
            print(f"Processing: {filepath.name}")
            chunks = process_file(filepath)
            all_chunks.extend(chunks)
            print(f"  Created {len(chunks)} chunks")

    return all_chunks


async def upsert_to_pinecone(
    chunks: List[PWSChunk],
    batch_size: int = 50,
    namespace: str = NAMESPACE,
) -> Dict[str, Any]:
    """Upsert chunks to Pinecone in batches"""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not set")

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {
            "Api-Key": PINECONE_API_KEY,
            "Content-Type": "application/json",
        }

        url = f"https://{INDEX_HOST}/records/namespaces/{namespace}/upsert"

        results = {
            "total_chunks": len(chunks),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            records = [chunk.to_pinecone_record() for chunk in batch]

            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"records": records},
                )
                response.raise_for_status()
                results["successful"] += len(batch)
                print(f"  Upserted batch {i//batch_size + 1}: {len(batch)} records")

            except Exception as e:
                results["failed"] += len(batch)
                results["errors"].append(str(e))
                print(f"  Failed batch {i//batch_size + 1}: {e}")

        return results


def save_chunks_for_review(chunks: List[PWSChunk], output_path: Path):
    """Save chunks to JSON for review before upserting"""
    records = [chunk.to_pinecone_record() for chunk in chunks]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(records)} chunks to {output_path}")
    print("Review the file, then run with --upsert flag to upload to Pinecone")


# ============================================================================
# MANUAL CONTENT ADDITION
# ============================================================================

def create_manual_chunks() -> List[PWSChunk]:
    """
    Create chunks from manually provided content.

    Use this when you have content that needs to be added directly
    (e.g., copied from Google Docs, PDFs, etc.)
    """
    chunks = []

    # Example: Add content here
    # chunks.append(PWSChunk(
    #     id="framework-example-1",
    #     content="Your content here...",
    #     title="Example Framework",
    #     category=Category.FRAMEWORK.value,
    #     type="manual",
    #     source="manual-entry",
    #     tags=["framework", "example"],
    #     problem_type=ProblemType.ILL_DEFINED.value,
    # ))

    return chunks


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="PWS Brain Ingestion Pipeline")
    parser.add_argument("--input-dir", type=str, help="Directory containing PWS materials")
    parser.add_argument("--output", type=str, default="pws_chunks.json", help="Output file for review")
    parser.add_argument("--upsert", action="store_true", help="Actually upsert to Pinecone")
    parser.add_argument("--namespace", type=str, default=NAMESPACE, help="Pinecone namespace")
    parser.add_argument("--manual", action="store_true", help="Use manual content addition")

    args = parser.parse_args()

    if args.manual:
        chunks = create_manual_chunks()
    elif args.input_dir:
        input_path = Path(args.input_dir)
        if not input_path.exists():
            print(f"Error: Directory {input_path} does not exist")
            exit(1)
        chunks = process_directory(input_path)
    else:
        print("Error: Provide --input-dir or --manual flag")
        parser.print_help()
        exit(1)

    if not chunks:
        print("No chunks created. Check your input.")
        exit(1)

    print(f"\nTotal chunks created: {len(chunks)}")

    # Show category distribution
    categories = {}
    for chunk in chunks:
        categories[chunk.category] = categories.get(chunk.category, 0) + 1
    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    if args.upsert:
        print(f"\nUpserting to Pinecone namespace: {args.namespace}")
        results = asyncio.run(upsert_to_pinecone(chunks, namespace=args.namespace))
        print(f"\nResults:")
        print(f"  Successful: {results['successful']}")
        print(f"  Failed: {results['failed']}")
        if results['errors']:
            print(f"  Errors: {results['errors']}")
    else:
        save_chunks_for_review(chunks, Path(args.output))
