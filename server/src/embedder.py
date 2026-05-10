import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiEmbedder:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"
        print(f"Using Gemini embedding model: {self.model}")
        
    def embed_text(self, text: str, title: str = "none") -> list[float]:
        """Generates a 768-dimensional embedding using Gemini."""
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
            title=title
        )
        return result['embedding']
        
    def embed_query(self, query: str) -> list[float]:
        """Generates an embedding for a search query using Gemini."""
        result = genai.embed_content(
            model=self.model,
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']
