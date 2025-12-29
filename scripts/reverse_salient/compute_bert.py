#!/usr/bin/env python3
"""
Compute semantic similarity using BERT embeddings.
Based on sts_bert.py implementation.
"""
import numpy as np
import json
import torch
from transformers import BertModel, BertTokenizer
from sklearn.metrics.pairwise import cosine_similarity

def predict_by_segments(model, tokenized_ids, max_length=512):
    """
    Handle documents longer than BERT's max length by processing in segments.
    
    Args:
        model: BERT model
        tokenized_ids: Tensor of token IDs
        max_length: Maximum segment length (default: 512)
        
    Returns:
        Combined embeddings from all segments
    """
    segments = []
    size = tokenized_ids.shape[1]
    index = 0
    
    while size >= max_length:
        segment = tokenized_ids[:, index:index+max_length]
        predicted = model(segment)
        embedding = predicted.last_hidden_state[:, 0, :]  # CLS token
        segments.append(embedding)
        
        index += max_length
        size -= max_length
    
    # Process remaining tokens
    if size > 0:
        segment = tokenized_ids[:, index:]
        predicted = model(segment)
        embedding = predicted.last_hidden_state[:, 0, :]
        segments.append(embedding)
    
    # Combine segments
    combined = torch.cat(segments, dim=0)
    return combined

def compute_bert_similarity(documents, bert_version='bert-large-cased'):
    """
    Compute semantic similarity matrix using BERT embeddings.
    
    Args:
        documents: List of document dicts with 'cleaned_text' field
        bert_version: BERT model version (default: 'bert-large-cased')
        
    Returns:
        similarity_matrix: NxN numpy array of semantic similarities [0,1]
    """
    print(f"Loading BERT model: {bert_version}...")
    tokenizer = BertTokenizer.from_pretrained(bert_version)
    model = BertModel.from_pretrained(bert_version)
    model.eval()
    
    # Generate embeddings
    embeddings_list = []
    n_docs = len(documents)
    
    print(f"Computing embeddings for {n_docs} documents...")
    
    with torch.no_grad():
        for idx, doc in enumerate(documents):
            # Tokenize
            tokens = tokenizer.tokenize(doc['cleaned_text'])
            token_ids = tokenizer.convert_tokens_to_ids(tokens)
            token_tensor = torch.tensor(token_ids).unsqueeze(0)
            
            # Get embedding
            embedding = predict_by_segments(model, token_tensor)
            embeddings_list.append(embedding)
            
            if (idx + 1) % 50 == 0:
                print(f"  Embedded {idx + 1}/{n_docs} documents")
    
    # Compute pairwise similarity
    similarity_matrix = np.zeros((n_docs, n_docs))
    
    print("Computing pairwise similarities...")
    for i in range(n_docs):
        for j in range(n_docs):
            # Compare all segment pairs
            similarities = []
            
            for seg_i in range(embeddings_list[i].shape[0]):
                for seg_j in range(embeddings_list[j].shape[0]):
                    emb_i = embeddings_list[i][seg_i].unsqueeze(0)
                    emb_j = embeddings_list[j][seg_j].unsqueeze(0)
                    
                    sim = cosine_similarity(
                        emb_i.numpy(),
                        emb_j.numpy()
                    )[0][0]
                    similarities.append(sim)
            
            # Average similarity across all segments
            similarity_matrix[i, j] = np.mean(similarities)
        
        if (i + 1) % 50 == 0:
            print(f"  Computed similarity for {i + 1}/{n_docs} documents")
    
    # Normalize to [0, 1] range
    min_val = np.min(similarity_matrix)
    max_val = np.max(similarity_matrix)
    
    if max_val > min_val:
        similarity_matrix = (similarity_matrix - min_val) / (max_val - min_val)
    
    print(f"BERT similarity matrix computed. Shape: {similarity_matrix.shape}")
    
    return similarity_matrix

def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: compute_bert.py <cleaned_documents.json> [output_matrix.npy] [--model bert-base-cased]")
        print("\nNote: Use bert-base-cased for faster computation, bert-large-cased for better quality")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = 'bert_similarity.npy'
    bert_version = 'bert-large-cased'
    
    # Parse arguments
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == '--model' and i + 1 < len(sys.argv):
            bert_version = sys.argv[i + 1]
        elif not arg.startswith('--') and arg != bert_version:
            output_file = arg
    
    with open(input_file, 'r') as f:
        documents = json.load(f)
    
    similarity_matrix = compute_bert_similarity(documents, bert_version)
    
    # Save similarity matrix
    np.save(output_file, similarity_matrix)
    print(f"Saved BERT similarity matrix to {output_file}")

if __name__ == '__main__':
    main()
