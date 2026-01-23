import fitz  # PyMuPDF #type: ignore
from typing import List, Dict, Any

def extract_hyperlinks(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts external HTTP/HTTPS hyperlinks from a PDF.
    Returns a list of dictionaries containing the page number and URL.
    """
    found_links = []

    try:
        # Use context manager to ensure the document closes automatically
        with fitz.open(pdf_path) as doc:
            # Iterate over each page
            for page_num, page in enumerate(doc):
                # get_links() returns a list of dictionaries representing links
                links = page.get_links()
                
                for link in links:
                    # We are interested in the 'uri' key
                    if "uri" in link:
                        url = link["uri"]
                        
                        # FILTER: strict check for http or https
                        if url.lower().startswith(("http://", "https://")):
                            found_links.append(url)
                            
    except Exception as e:
        print(f"Error extracting hyperlinks from PDF: {e}")
        return []
    
    return found_links


