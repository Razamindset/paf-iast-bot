import os
import hashlib
from supabase import create_client, Client

class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment")
        self.client: Client = create_client(url, key)
        self.table = "pafiast_documents"

    def chunk_exists(self, chunk_hash: str) -> bool:
        """Check if this exact text chunk has already been embedded and stored."""
        response = self.client.table(self.table).select("id").eq("chunk_hash", chunk_hash).execute()
        return len(response.data) > 0

    def insert_chunk(self, url: str, content: str, embedding: list[float]):
        """Inserts a single chunk and its embedding if it doesn't already exist."""
        chunk_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        if self.chunk_exists(chunk_hash):
            return False
            
        data = {
            "url": url,
            "content": content,
            "metadata": {"source": url},
            "embedding": embedding,
            "chunk_hash": chunk_hash
        }
        self.client.table(self.table).insert(data).execute()
        return True

    def search(self, query_embedding: list[float], limit: int = 3):
        """Searches for similar chunks using the match_documents Postgres function."""
        # Using the RPC (Remote Procedure Call) to invoke the match_documents function
        response = self.client.rpc(
            'match_documents', 
            {'query_embedding': query_embedding, 'match_threshold': 0.5, 'match_count': limit}
        ).execute()
        
        return response.data
