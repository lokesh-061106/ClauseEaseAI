"""
Text Summarization Service
Uses Hugging Face transformers for document summarization
"""

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    _AI_AVAILABLE = True
except Exception:
    torch = None
    AutoTokenizer = None
    AutoModelForSeq2SeqLM = None
    _AI_AVAILABLE = False
from typing import List
from pathlib import Path


class SummarizationService:
    """Handles AI-powered text summarization using Hugging Face models"""
    
    def __init__(self, model_name: str = 'facebook/bart-large-cnn', cache_dir: str = None):
        """
        Initialize summarization service
        
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
            print(f"Loading summarization model: {model_name}")
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
            print("Summarization model loaded successfully!")
        else:
            # Fallback: AI not available
            self.device = 'cpu'
            self.tokenizer = None
            self.model = None
            print("AI dependencies not available — running in fallback mode.")
    
    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 50,
        length_penalty: float = 2.0
    ) -> str:
        """
        Generate summary of input text
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            length_penalty: Length penalty for beam search
            
        Returns:
            Summary text
        """
        # If AI not available, return a simple fallback summary
        if not _AI_AVAILABLE or self.model is None or self.tokenizer is None:
            cleaned = text.replace('\n', ' ').strip()
            # Return first sentence or truncated text
            end = cleaned.find('.')
            if end != -1 and end < max_length:
                return cleaned[:end+1]
            return (cleaned[:max_length] + '...') if len(cleaned) > max_length else cleaned

        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            max_length=1024,
            truncation=True,
            padding=True
        ).to(self.device)

        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                **inputs,
                max_length=max_length,
                min_length=min_length,
                length_penalty=length_penalty,
                num_beams=4,
                early_stopping=True
            )

        # Decode summary
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        return summary.strip()
    
    def summarize_long_text(
        self,
        text: str,
        chunk_size: int = 800,
        final_max_length: int = 200
    ) -> str:
        """
        Summarize very long text by chunking and combining
        
        Args:
            text: Long input text
            chunk_size: Size of each chunk in characters
            final_max_length: Maximum length of final summary
            
        Returns:
            Combined summary
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
        
        # If only one chunk, summarize directly
        if len(chunks) == 1:
            return self.summarize(chunks[0], max_length=final_max_length)
        
        # Summarize each chunk
        chunk_summaries = []
        for chunk in chunks:
            summary = self.summarize(chunk, max_length=100, min_length=30)
            chunk_summaries.append(summary)
        
        # Combine and summarize again
        combined = ' '.join(chunk_summaries)
        final_summary = self.summarize(combined, max_length=final_max_length)
        
        return final_summary
    
    def batch_summarize(
        self,
        texts: List[str],
        max_length: int = 150
    ) -> List[str]:
        """
        Summarize multiple texts in batch
        
        Args:
            texts: List of input texts
            max_length: Maximum length of each summary
            
        Returns:
            List of summaries
        """
        return [self.summarize(text, max_length=max_length) for text in texts]


# Singleton instance
_summarization_service = None

def get_summarization_service(model_name: str = 'facebook/bart-large-cnn') -> SummarizationService:
    """Get or create singleton summarization service instance"""
    global _summarization_service
    if _summarization_service is None:
        _summarization_service = SummarizationService(model_name=model_name)
    return _summarization_service
