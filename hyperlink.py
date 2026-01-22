import fitz  # PyMuPDF #type: ignore

def extract_hyperlinks(pdf_path):
    """
    Extracts external HTTP/HTTPS hyperlinks from a PDF.
    Returns a list of dictionaries containing the page number and URL.
    """
    try:
        # Open the PDF document
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return []
    
    found_links = []

    # Iterate over each page
    for page_num, page in enumerate(doc):
        
        # get_links() returns a list of dictionaries representing links
        links = page.get_links()
        
        for link in links:
            # We are interested in 'uri' key
            if "uri" in link:
                url = link["uri"]
                
                # FILTER: strict check for http or https
                if url.lower().startswith(("http://", "https://")):
                    found_links.append({
                        "page": page_num + 1,  # Human-readable page number
                        "url": url
                    })
                
    doc.close()
    return found_links

