import os
from main import FastAPI, HTTPException #type: ignore
from pydantic import BaseModel  #type: ignore
from typing import List, Dict, Any, Optional
from mindee import ClientV2  #type: ignore
from openai import OpenAI  #type: ignore
from sentence_transformers import SentenceTransformer #type: ignore

# Import local services
from config import Config
from mindee_service import parse_resume_with_mindee
from pdf_service import extract_hyperlinks
from firecrawl_service import FirecrawlService
from openrouter_service import chat_with_reasoning_followup
from transformer_service import calculate_match_score


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
firecrawl_client: Optional[FirecrawlService] = None
try:
    if Config.FIRECRAWL_API_KEY:
        firecrawl_client = FirecrawlService(Config.FIRECRAWL_API_KEY)
    else:
        print("Warning: MINDEE_API_KEY not found in configuration.")
except Exception as e:
    print(f"Error initializing Mindee Client: {e}")

# Initialize openrouter Service
openrouter_client: Optional[OpenAI] = None
try:
    if Config.OPENROUTER_API_KEY:
        openrouter_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key= Config.OPENROUTER_API_KEY,
)
    else:
        print("Warning: MINDEE_API_KEY not found in configuration.")
except Exception as e:
    print(f"Error initializing Mindee Client: {e}")



ATS_client: Optional[OpenAI] = None
try:
    ATS_client = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Error initializing Mindee Client: {e}")

# --- Pydantic Models ---

class ResumeRequest(BaseModel):
    pdf_path: str

# NEW: Model for scoring request
class ScoreRequest(BaseModel):
    user_summary: str
    jd_summary: str

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

    #workflow_output = {
    #    "mindee_data": None,
    #    "extracted_links": [],
    #    "scraped_web_content": []
    #}
    workflow_output = []
    # Step 1: Mindee Parsing
    if mindee_client:
        print(f"Step 1: Parsing resume with Mindee: {pdf_path}")
        mindee_data = parse_resume_with_mindee(pdf_path, mindee_client)
        #workflow_output["mindee_data"] = mindee_data
        workflow_output.append(mindee_data)

    # Step 2: PDF Hyperlink Extraction
    print(f"Step 2: Extracting hyperlinks from PDF: {pdf_path}")
    # Returns List[Dict] like [{'page': 1, 'url': 'https://...'}]
    extracted_links = extract_hyperlinks(pdf_path)
    #workflow_output["extracted_links"] = extracted_links
    workflow_output.append(extracted_links)
    # Step 3: Firecrawl Scraping
    # Filter for valid URLs to scrape
    urls_to_scrape = extracted_links
    print(urls_to_scrape)
    if firecrawl_client and urls_to_scrape:
        print(f"Step 3: Scraping {len(urls_to_scrape)} URLs with Firecrawl")
        scraped_data = firecrawl_client.scrape_links(urls_to_scrape)
        workflow_output.append(scraped_data)
    
    #Step 4: LLM request
    final_message = chat_with_reasoning_followup(
            client=openrouter_client,
            initial_prompt=f"Use the information and create a detailted user profile info for a recruiter. User data extracted from multiple sources {workflow_output}",
            follow_up_prompt="Remove everything about thoughts of ai, return extact info of an user no more thoughts"
        )
    
    return { "resume_info" : final_message }


# NEW: Endpoint for Scoring
@app.post("/score_resume")
async def score_resume(request: ScoreRequest) -> Dict[str, Any]:
    """
    Calculates a semantic match score between a user summary and a job description (JD).
    Uses the pre-loaded SentenceTransformer model.
    """
    if not ATS_client:
        raise HTTPException(status_code=503, detail="ATS Model is not initialized.")

    try:
        score = calculate_match_score(
            user_summary=request.user_summary, 
            jd_summary=request.jd_summary, 
            model=ATS_client
        )
        return {
            "match_score": score,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Resume Parser Orchestrator"}


