#!/usr/bin/env python3
"""
Clean and preprocess documents for dual similarity analysis.
Based on paper_cleaning.py pattern.
"""
import re
import json
from typing import List, Dict

def clean_document(raw_text: str) -> str:
    """
    Clean a single document by removing metadata and normalizing text.
    
    Args:
        raw_text: Raw document text
        
    Returns:
        Cleaned text, or None if document should be skipped
    """
    text = raw_text
    
    # Skip documents without abstracts
    if "No abstract available" in text or "NO-ABSTRACT" in text:
        return None
    
    # Remove formatting characters
    text = text.replace("[", "").replace("]", "")
    text = text.replace("'", "").replace('"', "")
    text = text.replace("Â©", "COPYRIGHT")
    
    # Remove URLs and copyright notices
    text = re.sub(r'http\S*,', '', text)
    text = re.sub(r'Copyright.*', '', text)
    text = re.sub(r'COPYRIGHT.*', '', text)
    
    return text.strip()

def remove_stopwords(text: str) -> str:
    """
    Remove common stopwords for structural analysis.
    
    Args:
        text: Input text
        
    Returns:
        Text with stopwords removed
    """
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
    except:
        # Fallback basic stopword list if NLTK not available
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                     'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                     'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    tokens = text.split()
    filtered = [word for word in tokens if word.lower() not in stop_words]
    
    return ' '.join(filtered)

def process_documents(documents: List[Dict]) -> List[Dict]:
    """
    Process a list of documents for analysis.
    
    Args:
        documents: List of document dicts with 'text' field
        
    Returns:
        List of processed documents with cleaned_text and nostop_text fields
    """
    processed = []
    
    for doc in documents:
        cleaned = clean_document(doc.get('text', ''))
        
        if cleaned:
            processed.append({
                **doc,
                'cleaned_text': cleaned,
                'nostop_text': remove_stopwords(cleaned)
            })
    
    print(f"Processed {len(processed)}/{len(documents)} documents")
    return processed

def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: clean_documents.py <input.json> [output.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'cleaned_documents.json'
    
    with open(input_file, 'r') as f:
        documents = json.load(f)
    
    processed = process_documents(documents)
    
    with open(output_file, 'w') as f:
        json.dump(processed, f, indent=2)
    
    print(f"Saved {len(processed)} cleaned documents to {output_file}")

if __name__ == '__main__':
    main()
