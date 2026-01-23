import os
from fastapi import FastAPI, HTTPException #type: ignore
from pydantic import BaseModel  #type: ignore
from typing import List, Dict, Any, Optional
from mindee import ClientV2  #type: ignore

# Import local services
from config import Config
from mindee_service import parse_resume_with_mindee
from pdf_service import extract_hyperlinks
from firecrawl_service import FirecrawlService

# Initialize FastAPI App
app = FastAPI(title="Resume Parser API")

# --- Service Initialization ---

# Initialize Mindee Client
mindee_client: Optional[ClientV2] = None

try:
    if Config.MINDEE_API_KEY:
        mindee_client = ClientV2(api_key=Config.MINDEE_API_KEY)
    else:
        print("Warning: MINDEE_API_KEY not found in configuration.")
except Exception as e:
    print(f"Error initializing Mindee Client: {e}")

# Initialize Firecrawl Service
firecrawl_client = FirecrawlService(Config.FIRECRAWL_API_KEY)

# --- Pydantic Models ---

class ResumeRequest(BaseModel):
    pdf_path: str


# --- Endpoints ---

@app.post("/process_resume")
async def process_resume(request: ResumeRequest) -> Dict[str, Any]:
    """
    Orchestrates the resume processing workflow:
    1. Calls Mindee Service to parse the PDF.
    2. Calls PDF Service to extract hyperlinks.
    3. Calls Firecrawl Service to scrape content from extracted links.
    """
    pdf_path = request.pdf_path

    # Validate file existence
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"File not found: {pdf_path}")

    workflow_output = {
        "mindee_data": None,
        "extracted_links": [],
        "scraped_web_content": []
    }

    # Step 1: Mindee Parsing
    if mindee_client:
        print(f"Step 1: Parsing resume with Mindee: {pdf_path}")
        mindee_data = parse_resume_with_mindee(pdf_path, mindee_client)
        workflow_output["mindee_data"] = mindee_data
    else:
        workflow_output["mindee_data"] = {"error": "Mindee Service unavailable"}

    # Step 2: PDF Hyperlink Extraction
    print(f"Step 2: Extracting hyperlinks from PDF: {pdf_path}")
    # Returns List[Dict] like [{'page': 1, 'url': 'https://...'}]
    extracted_links = extract_hyperlinks(pdf_path)
    workflow_output["extracted_links"] = extracted_links

    # Step 3: Firecrawl Scraping
    # Filter for valid URLs to scrape
    urls_to_scrape = extracted_links
    print(urls_to_scrape)
    if firecrawl_client and urls_to_scrape:
        print(f"Step 3: Scraping {len(urls_to_scrape)} URLs with Firecrawl")
        scraped_data = firecrawl_client.scrape_links(urls_to_scrape)
        workflow_output["scraped_web_content"] = scraped_data
    elif not firecrawl_client:
        workflow_output["scraped_web_content"] = {"error": "Firecrawl Service unavailable"}
    else:
        workflow_output["scraped_web_content"] = {"message": "No URLs found to scrape"}

    return workflow_output


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Resume Parser Orchestrator"}


