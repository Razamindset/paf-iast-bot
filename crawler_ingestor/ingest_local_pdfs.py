import os
import json
import fitz  # PyMuPDF
import hashlib
from dotenv import load_dotenv
from src.embedder import LocalEmbedder
from src.database import SupabaseDB

PDF_DIR = "pdfs"

def chunk_text(text, chunk_size=800, overlap=100):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1
        if current_length >= chunk_size:
            chunks.append(" ".join(current_chunk))
            # Keep some words for overlap
            overlap_words = current_chunk[-overlap:] if overlap < len(current_chunk) else []
            current_chunk = overlap_words
            current_length = sum(len(w) + 1 for w in current_chunk)
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def extract_pdf_text(file_path):
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + " "
        doc.close()
    except Exception as e:
        print(f"  [!] Error reading PDF {file_path}: {e}")
    return text.strip()

def main():
    load_dotenv()
    
    print("Initializing Local PDF Ingestor...")
    embedder = LocalEmbedder()
    db = SupabaseDB()
    
    if not os.path.exists(PDF_DIR):
        print(f"  [!] PDF directory {PDF_DIR} not found. Run downloader first.")
        return

    files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    print(f"Found {len(files)} PDFs in {PDF_DIR}. Starting ingestion...")
    
    total_chunks = 0
    
    for filename in files:
        file_path = os.path.join(PDF_DIR, filename)
        meta_path = file_path + ".json"
        
        # Load metadata if available
        source_url = filename
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                source_url = meta.get('source_url', filename)
        
        print(f"\nProcessing: {filename}")
        text = extract_pdf_text(file_path)
        
        if not text or len(text) < 50:
            print(f"  [!] PDF is empty or too short, skipping.")
            continue
            
        chunks = chunk_text(text)
        print(f"  -> Extracted {len(chunks)} chunks. Embedding now...")
        
        for i, chunk in enumerate(chunks):
            if len(chunk) < 100:
                continue
            
            try:
                chunk_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()
                if db.chunk_exists(chunk_hash):
                    print(f"  [{i+1}/{len(chunks)}] Duplicate, skipping.")
                    continue
                
                print(f"  [{i+1}/{len(chunks)}] Embedding...", end=" ", flush=True)
                embedding = embedder.embed_text(chunk, title=filename)
                db.insert_chunk(source_url, chunk, embedding)
                total_chunks += 1
                print("Saved!")
                
            except Exception as e:
                print(f"\n  [!] Error on chunk {i+1}: {e}")
                
    print(f"\nIngestion Complete!")
    print(f"Total new chunks inserted: {total_chunks}")

if __name__ == "__main__":
    main()
