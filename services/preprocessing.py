"""
Text Preprocessing Service
Handles text cleaning, normalization, and preparation for NLP tasks
"""

import os
import re
import nltk
from typing import List, Dict
from pathlib import Path

# NLTK downloads are handled lazily if needed


class TextPreprocessor:
    """Handles text preprocessing and cleaning"""
    
    def __init__(self):
        """Initialize spaCy model for text processing"""
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            print(f"Warning: spaCy failed to load ({e}). Falling back to NLTK/Regex.")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\'\"]', '', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Remove multiple consecutive punctuation marks
        text = re.sub(r'([.,;:!?]){2,}', r'\1', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def segment_sentences(self, text: str) -> List[str]:
        """
        Segment text into sentences
        """
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        try:
            return nltk.sent_tokenize(text)
        except Exception:
            return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words using NLTK
        """
        try:
            return nltk.word_tokenize(text)
        except Exception:
            return text.split()
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities from text using spaCy or fallback
        """
        if self.nlp:
            doc = self.nlp(text)
            return [{'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char} for ent in doc.ents]
        return []
    
    def chunk_text(self, text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
        """
        Split long text into chunks for processing
        
        Args:
            text: Input text
            max_length: Maximum chunk length in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        sentences = self.segment_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > max_length and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > 1:
                    # Keep last sentence for overlap
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def preprocess(self, text: str) -> Dict[str, any]:
        """
        Complete preprocessing pipeline
        
        Args:
            text: Raw input text
            
        Returns:
            Dictionary with cleaned text, sentences, tokens, and entities
        """
        cleaned_text = self.clean_text(text)
        
        return {
            'cleaned_text': cleaned_text,
            'sentences': self.segment_sentences(cleaned_text),
            'tokens': self.tokenize(cleaned_text),
            'entities': self.extract_entities(cleaned_text),
            'word_count': len(self.tokenize(cleaned_text)),
            'sentence_count': len(self.segment_sentences(cleaned_text))
        }


# Singleton instance
_preprocessor = None

def get_preprocessor() -> TextPreprocessor:
    """Get or create singleton preprocessor instance"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = TextPreprocessor()
    return _preprocessor
