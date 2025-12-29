#!/usr/bin/env python3
"""
Detect reverse salient innovation opportunities from dual similarity matrices.
Based on comparison.py implementation.
"""
import numpy as np
import json
from typing import List, Dict, Tuple

def detect_reverse_salients(lsa_matrix: np.ndarray, 
                            bert_matrix: np.ndarray,
                            documents: List[Dict],
                            threshold: float = 0.30) -> List[Dict]:
    """
    Identify reverse salients by analyzing similarity differentials.
    
    Args:
        lsa_matrix: Structural similarity matrix (NxN)
        bert_matrix: Semantic similarity matrix (NxN)
        documents: List of document dicts
        threshold: Minimum differential score (default: 0.30)
        
    Returns:
        List of reverse salient candidates with scores and metadata
    """
    print(f"Detecting reverse salients with threshold={threshold}...")
    
    # Compute differential matrix
    differential_matrix = bert_matrix - lsa_matrix
    abs_differential = np.abs(differential_matrix)
    
    # Find high-differential pairs
    candidates = []
    n_docs = lsa_matrix.shape[0]
    
    for i in range(n_docs):
        for j in range(i + 1, n_docs):  # Upper triangle only
            
            diff_score = abs_differential[i, j]
            lsa_score = lsa_matrix[i, j]
            bert_score = bert_matrix[i, j]
            
            # Filter criteria
            if (diff_score > threshold and 
                lsa_score > 0.20 and 
                bert_score > 0.20):
                
                # Determine innovation type
                if lsa_score > bert_score:
                    innovation_type = "structural_transfer"
                    primary_similarity = "methods"
                    transfer_direction = "apply shared methods to different problems"
                else:
                    innovation_type = "semantic_implementation"
                    primary_similarity = "concepts"
                    transfer_direction = "implement shared concepts differently"
                
                candidates.append({
                    'doc_i': i,
                    'doc_j': j,
                    'differential': float(diff_score),
                    'lsa_similarity': float(lsa_score),
                    'bert_similarity': float(bert_score),
                    'innovation_type': innovation_type,
                    'primary_similarity': primary_similarity,
                    'transfer_direction': transfer_direction,
                    'doc_i_title': documents[i].get('title', f'Document {i}'),
                    'doc_j_title': documents[j].get('title', f'Document {j}'),
                    'doc_i_abstract': documents[i].get('abstract', ''),
                    'doc_j_abstract': documents[j].get('abstract', '')
                })
    
    # Sort by differential score (highest first)
    candidates.sort(key=lambda x: x['differential'], reverse=True)
    
    print(f"Found {len(candidates)} reverse salient candidates")
    if candidates:
        print(f"Top differential score: {candidates[0]['differential']:.3f}")
    
    return candidates

def rank_opportunities(candidates: List[Dict], top_n: int = 20) -> List[Dict]:
    """
    Rank reverse salients by breakthrough potential.
    
    Args:
        candidates: List of reverse salient candidates
        top_n: Number of top opportunities to return
        
    Returns:
        Top N opportunities ranked by breakthrough potential
    """
    for candidate in candidates:
        # Calculate composite scores
        diff_score = candidate['differential']
        min_sim = min(candidate['lsa_similarity'], candidate['bert_similarity'])
        
        # Novelty score (higher differential = more novel)
        novelty = diff_score
        
        # Feasibility score (higher minimum similarity = more feasible)
        feasibility = min_sim
        
        # Composite breakthrough potential (weight novelty more)
        breakthrough_potential = (novelty * 0.7) + (feasibility * 0.3)
        
        candidate['novelty_score'] = float(novelty)
        candidate['feasibility_score'] = float(feasibility)
        candidate['breakthrough_potential'] = float(breakthrough_potential)
    
    # Re-sort by breakthrough potential
    candidates.sort(key=lambda x: x['breakthrough_potential'], reverse=True)
    
    return candidates[:top_n]

def generate_innovation_thesis(reverse_salient: Dict, idx: int) -> Dict:
    """
    Transform reverse salient into actionable innovation opportunity.
    
    Args:
        reverse_salient: Reverse salient candidate dict
        idx: Opportunity index
        
    Returns:
        Innovation opportunity with thesis and analysis
    """
    rs = reverse_salient
    
    doc_a = rs['doc_i_title']
    doc_b = rs['doc_j_title']
    innovation_type = rs['innovation_type']
    differential = rs['differential']
    
    # Generate innovation thesis based on type
    if innovation_type == "structural_transfer":
        thesis = (
            f"By applying methodologies from '{doc_a}' to address challenges in "
            f"'{doc_b}', breakthrough performance can be achieved because these "
            f"domains share technical approaches (LSA: {rs['lsa_similarity']:.2f}) "
            f"but serve fundamentally different applications (BERT: {rs['bert_similarity']:.2f}). "
            f"The {differential:.2f} differential suggests a proven method waiting "
            f"for novel application."
        )
    else:  # semantic_implementation
        thesis = (
            f"By implementing concepts from '{doc_b}' using techniques from "
            f"'{doc_a}', a critical gap can be bridged because these domains share "
            f"conceptual foundations (BERT: {rs['bert_similarity']:.2f}) but employ "
            f"different technical implementations (LSA: {rs['lsa_similarity']:.2f}). "
            f"The {differential:.2f} differential indicates ripe conceptual transfer "
            f"awaiting technical innovation."
        )
    
    opportunity = {
        'opportunity_id': f"RS-{idx:03d}",
        'title': f"{innovation_type.replace('_', ' ').title()} Opportunity",
        'innovation_thesis': thesis,
        'innovation_type': innovation_type,
        'differential_score': differential,
        'breakthrough_potential': rs['breakthrough_potential'],
        'documents': {
            'doc_a': {
                'title': doc_a,
                'abstract': rs['doc_i_abstract']
            },
            'doc_b': {
                'title': doc_b,
                'abstract': rs['doc_j_abstract']
            }
        },
        'metrics': {
            'structural_similarity': rs['lsa_similarity'],
            'semantic_similarity': rs['bert_similarity'],
            'differential': differential,
            'novelty': rs['novelty_score'],
            'feasibility': rs['feasibility_score']
        }
    }
    
    return opportunity

def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: detect_reverse_salients.py <lsa_matrix.npy> <bert_matrix.npy> <documents.json> [threshold]")
        print("\nOptional: threshold (default: 0.30)")
        sys.exit(1)
    
    lsa_file = sys.argv[1]
    bert_file = sys.argv[2]
    docs_file = sys.argv[3]
    threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.30
    
    # Load data
    print("Loading similarity matrices...")
    lsa_matrix = np.load(lsa_file)
    bert_matrix = np.load(bert_file)
    
    with open(docs_file, 'r') as f:
        documents = json.load(f)
    
    # Detect reverse salients
    candidates = detect_reverse_salients(lsa_matrix, bert_matrix, documents, threshold)
    
    # Rank opportunities
    top_opportunities = rank_opportunities(candidates, top_n=20)
    
    # Generate innovation opportunities
    opportunities = []
    for idx, rs in enumerate(top_opportunities[:10], 1):
        opp = generate_innovation_thesis(rs, idx)
        opportunities.append(opp)
    
    # Save results
    output_file = 'reverse_salients.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_candidates': len(candidates),
                'threshold': threshold,
                'top_differential': candidates[0]['differential'] if candidates else 0
            },
            'top_opportunities': opportunities,
            'all_candidates': candidates[:50]  # Top 50 for inspection
        }, f, indent=2)
    
    print(f"\nSaved results to {output_file}")
    print(f"\nTop 3 Opportunities:")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"\n{i}. {opp['opportunity_id']} ({opp['innovation_type']})")
        print(f"   Differential: {opp['differential_score']:.3f}")
        print(f"   Breakthrough Potential: {opp['breakthrough_potential']:.2f}")

if __name__ == '__main__':
    main()
