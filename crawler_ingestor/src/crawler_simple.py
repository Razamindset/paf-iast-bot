import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import fitz  # PyMuPDF
import io

class SimpleCrawler:
    def __init__(self, base_url, max_pages=50):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.max_pages = max_pages
        self.ignore_patterns = [
            '/202', '/tag/', '/author/', '/feed/', '/category/blog/', 
            '/events/', '/calendar/', '/page/', '.jpg', '.png', '.zip', '.mp4'
        ]

    def is_valid(self, url):
        parsed = urlparse(url)
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
                # Keep overlap
                overlap_words = current_chunk[-overlap:] if overlap < len(current_chunk) else []
                current_chunk = overlap_words
                current_length = sum(len(w) + 1 for w in current_chunk)
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def extract_html_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        text = soup.get_text(separator=' ')
        return re.sub(r'\s+', ' ', text).strip()

    def extract_pdf_text(self, pdf_bytes):
        text = ""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text() + " "
        except Exception as e:
            print(f"    [!] Error reading PDF: {e}")
        return re.sub(r'\s+', ' ', text).strip()

    def crawl(self):
        queue = [self.base_url]
        pages_crawled = 0

        while queue and pages_crawled < self.max_pages:
            url = queue.pop(0)
            if url in self.visited:
                continue
                
            self.visited.add(url)
            print(f"Crawling: {url}")
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                    
                content_type = response.headers.get('Content-Type', '').lower()
                text = ""
                
                # Check if it's HTML or PDF
                if 'application/pdf' in content_type:
                    print(f"  -> Found PDF! Extracting text...")
                    text = self.extract_pdf_text(response.content)
                elif 'text/html' in content_type:
                    html = response.text
                    text = self.extract_html_text(html)
                    
                    # Only HTML pages have internal links to discover
                    soup = BeautifulSoup(html, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        next_url = urljoin(url, a['href']).split('#')[0]
                        if self.is_valid(next_url) and next_url not in self.visited:
                            queue.append(next_url)
                else:
                    continue
                
                if text:
                    chunks = self.chunk_text(text)
                    yield url, chunks
                    pages_crawled += 1
                        
            except Exception as e:
                print(f"Error crawling {url}: {e}")
