import os
import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import fitz  # PyMuPDF
import re

from src.embedder import LocalEmbedder
from src.database import SupabaseDB

class PDFOnlyCrawler:
    def __init__(self, base_url, max_html_pages=300):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.max_html_pages = max_html_pages
        # Ignore things we know don't have good PDF links to speed up search
        self.ignore_patterns = [
            '/tag/', '/author/', '/feed/', '/category/blog/', 
            '/events/', '/calendar/', '/page/', '.jpg', '.png', '.zip', '.mp4'
        ]

    def is_valid_html_link(self, url):
        parsed = urlparse(url)
        
        # ALWAYS allow if it explicitly ends in .pdf
        if url.lower().endswith('.pdf'):
            return True
            
        if parsed.netloc != self.domain:
            return False
        if any(p in url.lower() for p in self.ignore_patterns):
            return False
        return True

    def chunk_text(self, text, chunk_size=800, overlap=100):
        """Splits text into chunks of approximately chunk_size characters."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                overlap_words = current_chunk[-overlap:] if overlap < len(current_chunk) else []
                current_chunk = overlap_words
                current_length = sum(len(w) + 1 for w in current_chunk)
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def extract_pdf_text(self, pdf_bytes):
        text = ""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text() + " "
        except Exception as e:
            print(f"    [!] Error reading PDF: {e}")
        return re.sub(r'\s+', ' ', text).strip()

    def crawl_pdfs(self, embedder, db):
        """
        Single-pass approach: crawl HTML pages and process each PDF
        immediately as it is discovered — no waiting.
        """
        html_queue = [self.base_url]
        seen_pdfs = set()
        pages_crawled = 0
        total_chunks_inserted = 0
        total_duplicates_skipped = 0
        total_pdfs_found = 0

        while html_queue and pages_crawled < self.max_html_pages:
            url = html_queue.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)

            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                if 'text/html' not in response.headers.get('Content-Type', '').lower():
                    continue

                print(f"Scanning: {url}")
                pages_crawled += 1

                soup = BeautifulSoup(response.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    next_url = urljoin(url, href).split('#')[0]

                    if next_url.lower().endswith('.pdf'):
                        if next_url in seen_pdfs:
                            continue
                        seen_pdfs.add(next_url)

                        # ---- Process PDF immediately ----
                        print(f"\n  📄 PDF Found: {next_url}")
                        try:
                            pdf_response = requests.get(next_url, timeout=30)
                            if pdf_response.status_code != 200:
                                print(f"  [!] Download failed (HTTP {pdf_response.status_code})")
                                continue

                            text = self.extract_pdf_text(pdf_response.content)
                            if not text or len(text) < 50:
                                print(f"  [!] PDF is empty or unreadable, skipping.")
                                continue

                            chunks = self.chunk_text(text)
                            total_pdfs_found += 1
                            print(f"  -> Extracted {len(chunks)} chunks. Embedding now...")

                            for i, chunk in enumerate(chunks):
                                if len(chunk) < 100:
                                    continue
                                try:
                                    chunk_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()
                                    if db.chunk_exists(chunk_hash):
                                        total_duplicates_skipped += 1
                                        print(f"  [{i+1}/{len(chunks)}] Duplicate, skipping.")
                                        continue
                                    print(f"  [{i+1}/{len(chunks)}] Embedding...", end=" ", flush=True)
                                    embedding = embedder.embed_text(chunk, title=next_url.split('/')[-1])
                                    db.insert_chunk(next_url, chunk, embedding)
                                    total_chunks_inserted += 1
                                    print("Saved!")
                                except Exception as e:
                                    print(f"\n  [!] Chunk {i+1} failed: {e}")

                            print(f"  ✅ Done! {total_chunks_inserted} chunks stored so far.")

                        except Exception as e:
                            print(f"  [!] Error processing PDF: {e}")
                        # ---- End PDF processing ----

                    elif self.is_valid_html_link(next_url) and next_url not in self.visited:
                        html_queue.append(next_url)

            except Exception as e:
                print(f"Error scanning {url}: {e}")

        print(f"\n{'='*50}")
        print(f"PDF Ingestion Complete!")
        print(f"PDFs Processed:        {total_pdfs_found}")
        print(f"Chunks Inserted:       {total_chunks_inserted}")
        print(f"Duplicates Skipped:    {total_duplicates_skipped}")
        print(f"{'='*50}")


def main():
    load_dotenv()

    print("Initializing PDF-Only Ingestion Pipeline...")
    crawler = PDFOnlyCrawler(base_url="https://paf-iast.edu.pk/", max_html_pages=300)
    embedder = LocalEmbedder()
    db = SupabaseDB()

    print("\nStarting crawl — PDFs will be ingested immediately as they are found!\n")
    crawler.crawl_pdfs(embedder, db)

if __name__ == "__main__":
    main()
