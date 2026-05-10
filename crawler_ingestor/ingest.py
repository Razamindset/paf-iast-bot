import os
import time
from dotenv import load_dotenv
from src.crawler_simple import SimpleCrawler
from src.embedder import LocalEmbedder
from src.database import SupabaseDB

def main():
    load_dotenv()
    
    print("Initializing PAF-IAST Ingestion Pipeline...")
    crawler = SimpleCrawler(base_url="https://paf-iast.edu.pk/", max_pages=100)
    embedder = LocalEmbedder()
    db = SupabaseDB()
    
    total_chunks_inserted = 0
    total_duplicates_skipped = 0
    
    print("Starting crawl and embed process...")
    for url, chunks in crawler.crawl():
        print(f"Processing {len(chunks)} chunks for {url}")
        for i, chunk in enumerate(chunks):
            # PRECAUTION 1: Skip extremely short, useless chunks
            if len(chunk) < 100:
                print(f"  [{i+1}/{len(chunks)}] Skipped (Too short: {len(chunk)} chars)")
                continue
                
            try:
                # PRECAUTION 2: Hash the chunk and check DB BEFORE calling Google API
                import hashlib
                chunk_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()
                
                if db.chunk_exists(chunk_hash):
                    total_duplicates_skipped += 1
                    print(f"  [{i+1}/{len(chunks)}] Skipped (Duplicate found in DB)")
                    continue
                    
                # 1. Embed the chunk
                print(f"  [{i+1}/{len(chunks)}] Generating local embedding... ", end="", flush=True)
                embedding = embedder.embed_text(chunk)
                
                # 2. Store in Supabase
                db.insert_chunk(url, chunk, embedding)
                total_chunks_inserted += 1
                print("Done & Saved to Supabase!")
            except Exception as e:
                print(f"\n  [{i+1}/{len(chunks)}] Failed to process chunk: {e}")
                
    print(f"\nIngestion Complete!")
    print(f"Successfully inserted: {total_chunks_inserted} new chunks")
    print(f"Skipped duplicates: {total_duplicates_skipped} chunks")

if __name__ == "__main__":
    main()
