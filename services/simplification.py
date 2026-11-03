"""
Text Simplification Service
Uses Hugging Face transformers for AI-powered text simplification
"""

import os
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    _AI_AVAILABLE = True
except Exception:
    torch = None
    AutoTokenizer = None
    AutoModelForSeq2SeqLM = None
    _AI_AVAILABLE = False
from typing import List, Dict
from pathlib import Path


class SimplificationService:
    """Handles AI-powered text simplification using Hugging Face models"""
    
    def __init__(self, model_name: str = 'google/flan-t5-small', cache_dir: str = None):
        """
        Initialize simplification service
        
        Args:
            model_name: Hugging Face model identifier
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or './model_cache'
        
        # Create cache directory
        try:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        
        # Determine device and load model if AI deps available
        if _AI_AVAILABLE:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Loading simplification model: {model_name}")
            print(f"Using device: {self.device}")
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            ).to(self.device)
            print("Model loaded successfully!")
        else:
            # Fallback: AI not available, use simple passthrough
            self.device = 'cpu'
            self.tokenizer = None
            self.model = None
            print("AI dependencies not available — running in fallback mode.")
    
    def simplify_text(
        self,
        text: str,
        level: str = 'intermediate',
        max_length: int = 512,
        temperature: float = 0.5
    ) -> str:
        """
        Simplify text using AI model
        
        Args:
            text: Input text to simplify
            level: Simplification level ('basic', 'intermediate', 'advanced')
            max_length: Maximum length of output
            temperature: Sampling temperature (higher = more creative)
            
        Returns:
            Simplified text
        """
        # Define prompts for different levels
        prompts = {
            'basic': 'Simplify the following legal text into very simple English that a 10-year-old can understand:\n\n',
            'intermediate': 'Simplify the following legal text into plain English:\n\n',
            'advanced': 'Rewrite the following legal text in clearer, more accessible language:\n\n'
        }
        
        prompt = prompts.get(level, prompts['intermediate'])
        input_text = prompt + text
        
        # If AI not available, return a simple cleaned/truncated fallback
        if not _AI_AVAILABLE or self.model is None:
            cleaned = input_text.replace('\n', ' ').strip()
            return (cleaned[:max_length] + '...') if len(cleaned) > max_length else cleaned

        # Tokenize input
        inputs = self.tokenizer(
            input_text,
            return_tensors='pt',
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)

        # Generate simplified text
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True if temperature > 0 else False,
                top_p=0.9,
                num_beams=4,
                early_stopping=True
            )

        # Decode output
        simplified_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return simplified_text.strip()
    
    def simplify_long_text(
        self,
        text: str,
        level: str = 'intermediate',
        chunk_size: int = 400
    ) -> str:
        """
        Simplify long text by processing in chunks
        
        Args:
            text: Long input text
            level: Simplification level
            chunk_size: Size of each chunk in characters
            
        Returns:
            Complete simplified text
        """
        # Import preprocessing here to avoid circular import
        from services.preprocessing import get_preprocessor
        
        preprocessor = get_preprocessor()
        sentences = preprocessor.segment_sentences(text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Simplify each chunk
        simplified_chunks = []
        for chunk in chunks:
            simplified = self.simplify_text(chunk, level=level)
            simplified_chunks.append(simplified)
        
        # Combine simplified chunks
        return ' '.join(simplified_chunks)
    
    def batch_simplify(
        self,
        texts: List[str],
        level: str = 'intermediate'
    ) -> List[str]:
        """
        Simplify multiple texts in batch
        
        Args:
            texts: List of input texts
            level: Simplification level
            
        Returns:
            List of simplified texts
        """
        return [self.simplify_text(text, level=level) for text in texts]


# Singleton instance
_simplification_service = None

def get_simplification_service(model_name: str = 'google/flan-t5-small') -> SimplificationService:
    """Get or create singleton simplification service instance"""
    global _simplification_service
    if _simplification_service is None:
        _simplification_service = SimplificationService(model_name=model_name)
    return _simplification_service
