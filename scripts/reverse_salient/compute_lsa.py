#!/usr/bin/env python3
"""
Compute structural similarity using Latent Semantic Analysis (LSA).
Based on lsa.py implementation.
"""
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

def compute_lsa_similarity(documents, n_components=80, max_features=2000):
    """
    Compute structural similarity matrix using LSA.
    
    Args:
        documents: List of document dicts with 'nostop_text' field
        n_components: Number of latent topics (default: 80)
        max_features: Maximum vocabulary size (default: 2000)
        
    Returns:
        similarity_matrix: NxN numpy array of structural similarities [0,1]
        topics: List of topic terms for inspection
    """
    # Extract preprocessed text (stopwords removed)
    texts = [doc['nostop_text'] for doc in documents]
    
    print(f"Computing LSA for {len(texts)} documents...")
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=max_features,
        max_df=0.5,  # Ignore terms in >50% of documents
        smooth_idf=True
    )
    
    X = vectorizer.fit_transform(texts)
    print(f"Document-term matrix shape: {X.shape}")
    
    # Apply SVD for dimensionality reduction
    svd_model = TruncatedSVD(
        n_components=n_components,
        algorithm='randomized',
        n_iter=10,
        random_state=256
    )
    
    svd_model.fit(X)
    
    # Extract topics
    terms = vectorizer.get_feature_names_out()
    topics = []
    
    for i, comp in enumerate(svd_model.components_):
        terms_comp = zip(terms, comp)
        sorted_terms = sorted(terms_comp, key=lambda x: x[1], reverse=True)[:7]
        topic_terms = [t[0] for t in sorted_terms]
        topics.append(topic_terms)
        
        if i < 10:  # Print first 10 topics
            print(f"Topic {i}: {', '.join(topic_terms)}")
    
    # Count topic occurrences in each document
    paper_topic_counts = []
    
    for doc_tokens in [doc['nostop_text'].split() for doc in documents]:
        topic_count = [0] * len(topics)
        
        for word in doc_tokens:
            for topic_idx, topic in enumerate(topics):
                if word in topic:
                    topic_count[topic_idx] += 1
        
        paper_topic_counts.append(topic_count)
    
    # Create normalized topic distribution matrix
    paper_topic_matrix = np.array(paper_topic_counts, dtype='float32')
    
    # Normalize rows
    row_sums = np.sum(paper_topic_matrix, axis=1)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    normalized_matrix = paper_topic_matrix / row_sums[:, np.newaxis]
    
    # Compute pairwise similarity using inverse L1 distance
    n_docs = len(documents)
    similarity_matrix = np.zeros((n_docs, n_docs))
    
    print("Computing pairwise similarities...")
    for i in range(n_docs):
        for j in range(n_docs):
            distance = np.sum(np.abs(normalized_matrix[i] - normalized_matrix[j]))
            similarity_matrix[i, j] = 1.0 - (distance / 2.0)
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{n_docs} documents")
    
    # Normalize to [0, 1] range
    min_val = np.min(similarity_matrix)
    max_val = np.max(similarity_matrix)
    
    if max_val > min_val:
        similarity_matrix = (similarity_matrix - min_val) / (max_val - min_val)
    
    print(f"LSA similarity matrix computed. Shape: {similarity_matrix.shape}")
    
    return similarity_matrix, topics

def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: compute_lsa.py <cleaned_documents.json> [output_matrix.npy]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'lsa_similarity.npy'
    
    with open(input_file, 'r') as f:
        documents = json.load(f)
    
    similarity_matrix, topics = compute_lsa_similarity(documents)
    
    # Save similarity matrix
    np.save(output_file, similarity_matrix)
    print(f"Saved LSA similarity matrix to {output_file}")
    
    # Save topics
    topics_file = output_file.replace('.npy', '_topics.json')
    with open(topics_file, 'w') as f:
        json.dump(topics, f, indent=2)
    print(f"Saved topics to {topics_file}")

if __name__ == '__main__':
    main()
