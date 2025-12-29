"""
Reverse Salient Discovery Tools

Core tools for cross-domain innovation discovery using dual similarity analysis.
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

# Optional ML imports - gracefully degrade if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    from transformers import BertModel, BertTokenizer
    from sklearn.metrics.pairwise import cosine_similarity
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False


@dataclass
class Document:
    """Research document for analysis"""
    id: str
    title: str
    abstract: str
    text: str
    authors: List[str] = None
    date: str = None
    url: str = None
    cleaned_text: str = None
    nostop_text: str = None


@dataclass
class ReverseSalient:
    """Detected reverse salient opportunity"""
    opportunity_id: str
    innovation_type: str  # structural_transfer or semantic_implementation
    differential_score: float
    breakthrough_potential: float
    doc_a_title: str
    doc_b_title: str
    doc_a_abstract: str
    doc_b_abstract: str
    lsa_similarity: float
    bert_similarity: float
    innovation_thesis: str
    technical_pathway: List[str] = None


# =============================================================================
# TOOL 1: Search Research Documents
# =============================================================================

async def search_research_documents(
    domain_a: str,
    domain_b: str,
    num_queries: int = 15,
    max_results_per_query: int = 15,
    time_range: str = "3y",
) -> Dict[str, Any]:
    """
    Search for research documents across two domains using Tavily.

    Generates diverse queries covering:
    - Direct intersection queries
    - A→B transfer queries
    - B→A transfer queries

    Args:
        domain_a: First domain (e.g., "autonomous drone swarms")
        domain_b: Second domain (e.g., "naval fleet operations")
        num_queries: Number of queries to generate (default: 15)
        max_results_per_query: Results per query (default: 15)
        time_range: Time range for papers (default: "3y")

    Returns:
        Dict with documents and metadata
    """
    # Generate diverse search queries
    queries = []

    # Direct intersection queries (5)
    queries.extend([
        f'"{domain_a}" AND "{domain_b}"',
        f'{domain_a} {domain_b} research',
        f'{domain_a} {domain_b} innovation',
        f'cross-disciplinary {domain_a} {domain_b}',
        f'{domain_a} applied to {domain_b}',
    ])

    # A→B transfer queries (5)
    queries.extend([
        f'{domain_a} methods for {domain_b}',
        f'{domain_a} techniques {domain_b} applications',
        f'{domain_a} algorithms in {domain_b}',
        f'transfer {domain_a} to {domain_b}',
        f'{domain_a} solutions {domain_b} problems',
    ])

    # B→A transfer queries (5)
    queries.extend([
        f'{domain_b} concepts in {domain_a}',
        f'{domain_b} principles for {domain_a}',
        f'{domain_b} approaches to {domain_a}',
        f'{domain_b} insights for {domain_a}',
        f'{domain_b} frameworks {domain_a}',
    ])

    return {
        "status": "queries_generated",
        "domain_a": domain_a,
        "domain_b": domain_b,
        "queries": queries[:num_queries],
        "search_config": {
            "max_results_per_query": max_results_per_query,
            "time_range": time_range,
            "include_domains": [
                "arxiv.org",
                "nature.com",
                "science.org",
                "ieee.org",
                "pubmed.ncbi.nlm.nih.gov",
                "patents.google.com",
            ],
        },
        "instructions": """
Execute these queries using Tavily with the specified config.
For each result, extract:
- title
- abstract (or first paragraph)
- full text if available
- authors
- publication date
- URL/DOI

Save results as documents_raw.json
""",
    }


# =============================================================================
# TOOL 2: Clean Documents
# =============================================================================

def clean_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and preprocess documents for dual similarity analysis.

    Removes metadata, normalizes text, and creates separate versions
    for LSA (stopwords removed) and BERT (cleaned only).

    Args:
        documents: List of raw document dicts

    Returns:
        List of cleaned document dicts with cleaned_text and nostop_text
    """
    # Basic stopwords (extended)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'their', 'our', 'your', 'its', 'his', 'her', 'which', 'what', 'who',
        'whom', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just',
        'also', 'now', 'here', 'there', 'then', 'about', 'above', 'after',
        'again', 'against', 'any', 'because', 'before', 'below', 'between',
        'into', 'through', 'during', 'out', 'off', 'over', 'under', 'up',
    }

    def clean_text(raw_text: str) -> Optional[str]:
        """Clean a single document"""
        if not raw_text:
            return None

        text = raw_text

        # Skip documents without abstracts
        if "No abstract available" in text or "NO-ABSTRACT" in text:
            return None

        # Remove formatting characters
        text = text.replace("[", "").replace("]", "")
        text = text.replace("'", "").replace('"', "")
        text = text.replace("©", "COPYRIGHT")

        # Remove URLs and copyright notices
        text = re.sub(r'http\S*,?', '', text)
        text = re.sub(r'Copyright.*', '', text, flags=re.IGNORECASE)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def remove_stopwords(text: str) -> str:
        """Remove stopwords for LSA"""
        tokens = text.lower().split()
        filtered = [word for word in tokens if word not in stop_words and len(word) > 2]
        return ' '.join(filtered)

    processed = []

    for doc in documents:
        raw_text = doc.get('text') or doc.get('abstract', '')
        cleaned = clean_text(raw_text)

        if cleaned and len(cleaned) > 100:
            processed.append({
                **doc,
                'cleaned_text': cleaned,
                'nostop_text': remove_stopwords(cleaned),
            })

    return processed


# =============================================================================
# TOOL 3: Compute LSA Similarity
# =============================================================================

def compute_lsa_similarity(
    documents: List[Dict[str, Any]],
    n_components: int = 80,
    max_features: int = 2000,
) -> Tuple[np.ndarray, List[List[str]]]:
    """
    Compute structural similarity matrix using Latent Semantic Analysis.

    Measures shared terminology, methods, and technical approaches.
    High LSA similarity = domains share methods/vocabulary.

    Args:
        documents: List of cleaned documents with 'nostop_text' field
        n_components: Number of latent topics (default: 80)
        max_features: Maximum vocabulary size (default: 2000)

    Returns:
        Tuple of (similarity_matrix, topics)
        - similarity_matrix: NxN numpy array [0,1]
        - topics: List of topic term lists for inspection
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required for LSA computation. Install with: pip install scikit-learn")

    texts = [doc['nostop_text'] for doc in documents]
    n_docs = len(texts)

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=max_features,
        max_df=0.5,  # Ignore terms in >50% of documents
        smooth_idf=True,
    )

    X = vectorizer.fit_transform(texts)

    # Apply SVD for dimensionality reduction
    svd_model = TruncatedSVD(
        n_components=min(n_components, n_docs - 1),
        algorithm='randomized',
        n_iter=10,
        random_state=256,
    )

    svd_model.fit(X)

    # Extract topics
    terms = vectorizer.get_feature_names_out()
    topics = []

    for comp in svd_model.components_:
        sorted_indices = np.argsort(comp)[::-1][:7]
        topic_terms = [terms[i] for i in sorted_indices]
        topics.append(topic_terms)

    # Count topic occurrences in each document
    paper_topic_counts = np.zeros((n_docs, len(topics)))

    for doc_idx, doc in enumerate(documents):
        doc_tokens = set(doc['nostop_text'].split())
        for topic_idx, topic in enumerate(topics):
            paper_topic_counts[doc_idx, topic_idx] = sum(1 for term in topic if term in doc_tokens)

    # Normalize rows
    row_sums = np.sum(paper_topic_counts, axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    normalized_matrix = paper_topic_counts / row_sums

    # Compute pairwise similarity using inverse L1 distance
    similarity_matrix = np.zeros((n_docs, n_docs))

    for i in range(n_docs):
        for j in range(n_docs):
            distance = np.sum(np.abs(normalized_matrix[i] - normalized_matrix[j]))
            similarity_matrix[i, j] = 1.0 - (distance / 2.0)

    # Normalize to [0, 1] range
    min_val = np.min(similarity_matrix)
    max_val = np.max(similarity_matrix)

    if max_val > min_val:
        similarity_matrix = (similarity_matrix - min_val) / (max_val - min_val)

    return similarity_matrix, topics


# =============================================================================
# TOOL 4: Compute BERT Similarity
# =============================================================================

def compute_bert_similarity(
    documents: List[Dict[str, Any]],
    model_name: str = 'bert-base-cased',
    max_length: int = 512,
) -> np.ndarray:
    """
    Compute semantic similarity matrix using BERT embeddings.

    Measures conceptual alignment and meaning overlap.
    High BERT similarity = domains share concepts/problems.

    Args:
        documents: List of cleaned documents with 'cleaned_text' field
        model_name: BERT model (default: 'bert-base-cased', use 'bert-large-cased' for better quality)
        max_length: Maximum tokens per segment (default: 512)

    Returns:
        similarity_matrix: NxN numpy array [0,1]
    """
    if not BERT_AVAILABLE:
        raise ImportError("transformers and torch required for BERT. Install with: pip install transformers torch")

    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    model.eval()

    n_docs = len(documents)
    embeddings_list = []

    with torch.no_grad():
        for doc in documents:
            text = doc['cleaned_text'][:10000]  # Limit text length

            # Tokenize
            tokens = tokenizer.tokenize(text)
            token_ids = tokenizer.convert_tokens_to_ids(tokens)

            # Process in segments
            segment_embeddings = []
            for start in range(0, len(token_ids), max_length):
                segment = token_ids[start:start + max_length]
                token_tensor = torch.tensor([segment])

                output = model(token_tensor)
                embedding = output.last_hidden_state[:, 0, :].numpy()
                segment_embeddings.append(embedding)

            if segment_embeddings:
                # Average across segments
                doc_embedding = np.mean(np.vstack(segment_embeddings), axis=0)
            else:
                doc_embedding = np.zeros(model.config.hidden_size)

            embeddings_list.append(doc_embedding)

    # Stack into matrix
    embeddings_matrix = np.vstack(embeddings_list)

    # Compute pairwise cosine similarity
    similarity_matrix = cosine_similarity(embeddings_matrix)

    # Normalize to [0, 1] range
    min_val = np.min(similarity_matrix)
    max_val = np.max(similarity_matrix)

    if max_val > min_val:
        similarity_matrix = (similarity_matrix - min_val) / (max_val - min_val)

    return similarity_matrix


# =============================================================================
# TOOL 5: Detect Reverse Salients
# =============================================================================

def detect_reverse_salients(
    lsa_matrix: np.ndarray,
    bert_matrix: np.ndarray,
    documents: List[Dict[str, Any]],
    threshold: float = 0.30,
    min_similarity: float = 0.20,
    top_n: int = 20,
) -> List[ReverseSalient]:
    """
    Identify reverse salient innovation opportunities.

    Finds document pairs where structural (LSA) and semantic (BERT) similarity
    diverge significantly, indicating transferable knowledge.

    Args:
        lsa_matrix: Structural similarity matrix
        bert_matrix: Semantic similarity matrix
        documents: List of documents
        threshold: Minimum differential score (default: 0.30)
        min_similarity: Minimum similarity in both matrices (default: 0.20)
        top_n: Number of top opportunities to return (default: 20)

    Returns:
        List of ReverseSalient opportunities ranked by breakthrough potential
    """
    n_docs = lsa_matrix.shape[0]
    candidates = []

    for i in range(n_docs):
        for j in range(i + 1, n_docs):
            lsa_score = lsa_matrix[i, j]
            bert_score = bert_matrix[i, j]
            diff_score = abs(bert_score - lsa_score)

            # Filter criteria
            if (diff_score > threshold and
                lsa_score > min_similarity and
                bert_score > min_similarity):

                # Determine innovation type
                if lsa_score > bert_score:
                    innovation_type = "structural_transfer"
                    thesis_template = (
                        "By applying methodologies from '{doc_a}' to address challenges in "
                        "'{doc_b}', breakthrough performance can be achieved. These domains share "
                        "technical approaches (LSA: {lsa:.2f}) but serve different applications "
                        "(BERT: {bert:.2f}). The {diff:.2f} differential suggests a proven method "
                        "waiting for novel application."
                    )
                else:
                    innovation_type = "semantic_implementation"
                    thesis_template = (
                        "By implementing concepts from '{doc_b}' using techniques from '{doc_a}', "
                        "a critical gap can be bridged. These domains share conceptual foundations "
                        "(BERT: {bert:.2f}) but employ different implementations (LSA: {lsa:.2f}). "
                        "The {diff:.2f} differential indicates ripe conceptual transfer awaiting "
                        "technical innovation."
                    )

                # Calculate breakthrough potential
                novelty = diff_score
                feasibility = min(lsa_score, bert_score)
                breakthrough_potential = (novelty * 0.7) + (feasibility * 0.3)

                # Generate thesis
                doc_a_title = documents[i].get('title', f'Document {i}')
                doc_b_title = documents[j].get('title', f'Document {j}')

                thesis = thesis_template.format(
                    doc_a=doc_a_title,
                    doc_b=doc_b_title,
                    lsa=lsa_score,
                    bert=bert_score,
                    diff=diff_score,
                )

                candidates.append(ReverseSalient(
                    opportunity_id=f"RS-{len(candidates)+1:03d}",
                    innovation_type=innovation_type,
                    differential_score=float(diff_score),
                    breakthrough_potential=float(breakthrough_potential),
                    doc_a_title=doc_a_title,
                    doc_b_title=doc_b_title,
                    doc_a_abstract=documents[i].get('abstract', '')[:500],
                    doc_b_abstract=documents[j].get('abstract', '')[:500],
                    lsa_similarity=float(lsa_score),
                    bert_similarity=float(bert_score),
                    innovation_thesis=thesis,
                ))

    # Sort by breakthrough potential
    candidates.sort(key=lambda x: x.breakthrough_potential, reverse=True)

    return candidates[:top_n]


# =============================================================================
# TOOL 6: Generate Opportunity Report
# =============================================================================

def generate_opportunity_report(
    opportunities: List[ReverseSalient],
    domain_a: str,
    domain_b: str,
    total_documents: int,
) -> str:
    """
    Generate executive summary report of innovation opportunities.

    Args:
        opportunities: List of detected ReverseSalient opportunities
        domain_a: First domain name
        domain_b: Second domain name
        total_documents: Total documents analyzed

    Returns:
        Markdown report string
    """
    if not opportunities:
        return f"""# Reverse Salient Innovation Report
## {domain_a} × {domain_b}

### Summary
Analyzed {total_documents} documents. No significant reverse salients detected.

This may indicate:
- Domains are too similar (already heavily cross-pollinated)
- Domains are too distant (no plausible connection mechanism)
- Consider adjusting threshold or expanding document corpus
"""

    avg_diff = sum(o.differential_score for o in opportunities) / len(opportunities)

    report = f"""# Reverse Salient Innovation Report
## {domain_a} × {domain_b}

### Executive Summary

Analyzed **{total_documents} documents** and identified **{len(opportunities)} high-potential
innovation opportunities** with average differential score of **{avg_diff:.2f}**.

---

### Top Opportunities

"""

    for i, opp in enumerate(opportunities[:5], 1):
        report += f"""#### {i}. {opp.opportunity_id}: {opp.innovation_type.replace('_', ' ').title()}

**Differential Score**: {opp.differential_score:.3f} | **Breakthrough Potential**: {opp.breakthrough_potential:.2f}

**Innovation Thesis**: {opp.innovation_thesis}

**Documents**:
- Domain A: {opp.doc_a_title}
- Domain B: {opp.doc_b_title}

**Metrics**:
- Structural Similarity (LSA): {opp.lsa_similarity:.2f}
- Semantic Similarity (BERT): {opp.bert_similarity:.2f}
- Differential: {opp.differential_score:.2f}

---

"""

    # Strategic recommendations
    structural_count = sum(1 for o in opportunities if o.innovation_type == "structural_transfer")
    semantic_count = len(opportunities) - structural_count

    report += f"""### Strategic Recommendations

**Pattern Analysis**:
- Structural Transfer Opportunities: {structural_count} ({structural_count/len(opportunities)*100:.0f}%)
- Semantic Implementation Opportunities: {semantic_count} ({semantic_count/len(opportunities)*100:.0f}%)

**Recommended Next Steps**:
1. Validate top 3 opportunities with domain experts
2. Conduct patent landscape search for each opportunity
3. Identify potential implementation partners
4. Define proof-of-concept scope for highest-potential opportunity

---

### Opportunity Quality Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| Total Candidates | {len(opportunities)} | {"Good" if 10 <= len(opportunities) <= 50 else "Review threshold"} |
| Top Differential | {opportunities[0].differential_score:.3f} | {"Excellent" if opportunities[0].differential_score > 0.40 else "Good" if opportunities[0].differential_score > 0.30 else "Moderate"} |
| Avg Breakthrough Potential | {sum(o.breakthrough_potential for o in opportunities)/len(opportunities):.2f} | {"High" if avg_diff > 0.45 else "Medium"} |

---

*Generated by Mindrian Reverse Salient Discovery Agent*
"""

    return report
