import os
import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException #type: ignore
from pydantic import BaseModel #type: ignore

# Service Imports
from mindee import Client #type: ignore
from mindee import ClientV2 #type: ignore
from mindee_service import parse_resume_with_mindee
from firecrawl_service import FirecrawlService
from pdf_service import extract_hyperlinks
from config import Config

# --- Helper Wrapper for Blocking Code ---
async def run_blocking_task(func, *args):
    """Runs synchronous (blocking) code in a separate thread."""
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func, *args)

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executes on startup and shutdown. 
    Initializes connections once and stores them in app.state.
    """
    print("🚀 Starting up: Initializing API Clients...")
    
    # Initialize clients and store in app.state
    app.state.firecrawl = FirecrawlService(Config.FIRECRAWL_API_KEY)
    app.state.mindee = mindee = ClientV2(api_key='md_rSSY4sX-Tullrv-aHUPeQTRx_YvW0PWzlTQ37lwqRqY')
    
    yield  # The application runs here
    
    print("🛑 Shutting down: Cleaning up resources...")
    # Clear references (optional in Python, but good practice)
    del app.state.firecrawl
    del app.state.mindee

app = FastAPI(lifespan=lifespan)

# --- Request Model ---
class ResumeRequest(BaseModel):
    file_path: str

# --- Response Models (Optional but recommended for documentation) ---
class ResumeResponse(BaseModel):
    status: str
    resume_analysis: Optional[Dict[str, Any]]
    external_links_found: int
    scraped_links_content: List[Dict[str, Any]]

# --- Endpoints ---

@app.post("/process-resume", response_model=ResumeResponse)
async def process_resume(request: ResumeRequest):
    """
    Orchestrates the entire flow:
    1. Extracts links (PyMuPDF)
    2. Parses Resume (Mindee)
    3. Scrapes Links (Firecrawl)
    """
    
    # 1. Validation
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    print(f"Processing: {request.file_path}")

    # 2. Parallel Execution
    # Task A: Extract Hyperlinks (CPU bound)
    links_task = run_blocking_task(extract_hyperlinks, request.file_path)
    
    # Task B: Parse Resume with Mindee (Network bound)
    # Access the global client via app.state.mindee
    mindee_task = run_blocking_task(
        parse_resume_with_mindee, 
        request.file_path, 
        app.state.mindee 
    )

    # Wait for both A and B to finish
    hyperlinks_data, resume_data = await asyncio.gather(links_task, mindee_task)

    # 3. Scrape the Found Links (Firecrawl)
    scraped_content = []
    
    if hyperlinks_data:
        # Extract just the URL strings
        url_list = [item['url'] for item in hyperlinks_data]
        
        # Access the global client via app.state.firecrawl
        scraped_content = await run_blocking_task(
            app.state.firecrawl.scrape_links, 
            url_list
        )

    # 4. Return Final Combined Response
    return {
        "status": "success",
        "resume_analysis": resume_data,
        "external_links_found": len(hyperlinks_data),
        "scraped_links_content": scraped_content
    }

@app.get("/")
def read_root():
    return {"message": "Resume Parser API is Online 🟢"}

if __name__ == "__main__":
    import uvicorn #type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)