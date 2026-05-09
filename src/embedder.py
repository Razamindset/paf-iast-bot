from google import genai
from google.genai import types
import os

class GoogleEmbedder:
    def __init__(self):
        # The new SDK automatically picks up GOOGLE_API_KEY from the environment
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment")
        self.client = genai.Client()
        self.model = 'gemini-embedding-2'
        
    def embed_text(self, text: str, title: str = "none") -> list[float]:
        """Generates a 768-dimensional embedding for the given document text."""
        # For gemini-embedding-2, document format is: 'title: {title} | text: {content}'
        formatted_content = f"title: {title} | text: {text}"
        
        result = self.client.models.embed_content(
            model=self.model,
            contents=formatted_content,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return result.embeddings[0].values
        
    def embed_query(self, query: str) -> list[float]:
        """Generates an embedding for a search query."""
        # For gemini-embedding-2, query format is: 'task: search result | query: {query}'
        formatted_query = f"task: search result | query: {query}"
        
        result = self.client.models.embed_content(
            model=self.model,
            contents=formatted_query,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return result.embeddings[0].values
