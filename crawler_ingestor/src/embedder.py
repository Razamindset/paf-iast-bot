from sentence_transformers import SentenceTransformer

class LocalEmbedder:
    def __init__(self):
        print("Loading local embedding model (all-mpnet-base-v2). This may take a minute on the first run as it downloads...")
        # all-mpnet-base-v2 produces 768-dimensional vectors, exactly matching your Supabase setup!
        self.model = SentenceTransformer('all-mpnet-base-v2')
        
    def embed_text(self, text: str, title: str = "none") -> list[float]:
        """Generates a 768-dimensional embedding for the given document text."""
        formatted_content = f"title: {title} | text: {text}"
        
        # Encode returns a numpy array, we convert to list for Supabase
        embedding = self.model.encode(formatted_content)
        return embedding.tolist()
        
    def embed_query(self, query: str) -> list[float]:
        """Generates an embedding for a search query."""
        formatted_query = f"task: search result | query: {query}"
        
        embedding = self.model.encode(formatted_query)
        return embedding.tolist()
