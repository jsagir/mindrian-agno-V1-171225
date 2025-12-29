#!/usr/bin/env python3
"""
Generate visualizations for reverse salient analysis.
"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import sys

def create_similarity_comparison(lsa_matrix, bert_matrix, output_dir='.'):
    """Create side-by-side comparison of similarity matrices"""
    differential_matrix = bert_matrix - lsa_matrix
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # LSA Similarity
    sns.heatmap(lsa_matrix, ax=axes[0], cmap='viridis', 
                cbar_kws={'label': 'Similarity'})
    axes[0].set_title('Structural Similarity (LSA)', fontsize=14)
    
    # BERT Similarity
    sns.heatmap(bert_matrix, ax=axes[1], cmap='viridis',
                cbar_kws={'label': 'Similarity'})
    axes[1].set_title('Semantic Similarity (BERT)', fontsize=14)
    
    # Differential
    sns.heatmap(differential_matrix, ax=axes[2], cmap='RdBu_r', center=0,
                cbar_kws={'label': 'Differential'})
    axes[2].set_title('Differential (BERT - LSA)', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/similarity_comparison.png', dpi=300)
    plt.close()
    print(f"Saved similarity comparison to {output_dir}/similarity_comparison.png")

def create_opportunity_chart(opportunities, output_dir='.'):
    """Create ranked opportunity bar chart"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    differentials = [opp['differential_score'] for opp in opportunities]
    types = [opp['innovation_type'] for opp in opportunities]
    labels = [opp['opportunity_id'] for opp in opportunities]
    
    colors = ['#FF6B6B' if t == 'structural_transfer' else '#4ECDC4' 
              for t in types]
    
    bars = ax.barh(range(len(differentials)), differentials, color=colors)
    ax.set_yticks(range(len(differentials)))
    ax.set_yticklabels(labels)
    ax.set_xlabel('Differential Score', fontsize=12)
    ax.set_title(f'Top {len(opportunities)} Reverse Salient Opportunities', fontsize=14)
    ax.invert_yaxis()
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#FF6B6B', label='Structural Transfer'),
        Patch(facecolor='#4ECDC4', label='Semantic Implementation')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/top_opportunities.png', dpi=300)
    plt.close()
    print(f"Saved opportunity chart to {output_dir}/top_opportunities.png")

def create_landscape_plot(candidates, output_dir='.'):
    """Create novelty vs feasibility scatter plot"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    differentials = [c['differential'] for c in candidates]
    feasibilities = [c['feasibility_score'] for c in candidates]
    types = [c['innovation_type'] for c in candidates]
    
    colors = ['red' if t == 'structural_transfer' else 'blue' for t in types]
    
    ax.scatter(differentials, feasibilities, c=colors, alpha=0.6, s=100)
    ax.set_xlabel('Novelty (Differential Score)', fontsize=12)
    ax.set_ylabel('Feasibility (Min Similarity)', fontsize=12)
    ax.set_title('Innovation Opportunity Landscape', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    # Quadrants
    if differentials:
        median_diff = np.median(differentials)
        median_feas = np.median(feasibilities)
        ax.axhline(y=median_feas, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=median_diff, color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/opportunity_landscape.png', dpi=300)
    plt.close()
    print(f"Saved landscape plot to {output_dir}/opportunity_landscape.png")

def main():
    if len(sys.argv) < 4:
        print("Usage: visualize_results.py <lsa_matrix.npy> <bert_matrix.npy> <reverse_salients.json> [output_dir]")
        sys.exit(1)
    
    lsa_file = sys.argv[1]
    bert_file = sys.argv[2]
    results_file = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else '.'
    
    # Load data
    lsa_matrix = np.load(lsa_file)
    bert_matrix = np.load(bert_file)
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    opportunities = results.get('top_opportunities', [])
    candidates = results.get('all_candidates', [])
    
    # Generate visualizations
    create_similarity_comparison(lsa_matrix, bert_matrix, output_dir)
    create_opportunity_chart(opportunities, output_dir)
    create_landscape_plot(candidates[:50], output_dir)  # Top 50 for clarity
    
    print(f"\nGenerated 3 visualizations in {output_dir}/")

if __name__ == '__main__':
    main()
