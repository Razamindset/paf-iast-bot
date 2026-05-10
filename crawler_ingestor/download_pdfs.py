import os
import requests
import json
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# List of URLs provided by the user
SOURCE_URLS = [
    "https://paf-iast.edu.pk/downloadnewstudents/",
    "https://paf-iast.edu.pk/for-existing-students/",
    "https://paf-iast.edu.pk/students-guides-policies/",
    "https://paf-iast.edu.pk/user-guides-proformas/",
    "https://paf-iast.edu.pk/news-letter/",
    "https://paf-iast.edu.pk/academic_schedules/",
    "https://paf-iast.edu.pk/admission-ads/",
    "https://paf-iast.edu.pk/notice-board/",
    "https://paf-iast.edu.pk/paf-iastbudgetreport/",
    "https://paf-iast.edu.pk/act-statutes/"
]

PDF_DIR = "pdfs"

def download_pdf(url):
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Create a safe filename
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Add hash to avoid collisions if filenames are same
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{url_hash}_{filename}"
            
            file_path = os.path.join(PDF_DIR, filename)
            meta_path = file_path + ".json"
            
            # Save PDF
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Save Metadata
            metadata = {
                "source_url": url,
                "filename": filename,
                "size_bytes": len(response.content),
                "downloaded_from": url
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            print(f"  [+] Downloaded: {filename}")
            return True
    except Exception as e:
        print(f"  [!] Error downloading {url}: {e}")
    return False

def main():
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        
    print(f"Starting PDF downloader in {PDF_DIR}...")
    
    total_downloaded = 0
    seen_pdfs = set()
    
    for page_url in SOURCE_URLS:
        print(f"Scanning: {page_url}")
        try:
            response = requests.get(page_url, timeout=15)
            if response.status_code != 200:
                print(f"  [!] Failed to load page (HTTP {response.status_code})")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href'].strip()
                pdf_url = urljoin(page_url, href)
                
                # Check if it's a PDF
                if pdf_url.lower().endswith('.pdf') and pdf_url not in seen_pdfs:
                    seen_pdfs.add(pdf_url)
                    if download_pdf(pdf_url):
                        total_downloaded += 1
                        
        except Exception as e:
            print(f"  [!] Error scanning {page_url}: {e}")
            
    print(f"\nDownload Complete!")
    print(f"Total PDFs downloaded: {total_downloaded}")

if __name__ == "__main__":
    main()
