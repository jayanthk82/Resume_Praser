import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import List

from fastapi import FastAPI, HTTPException  #type: ignore
from pydantic import BaseModel   #type: ignore

# Import your existing logic functions
# Assuming these are in local files as per your import statements
from mindee import Client  #type: ignore
from mindee_logic import parse_resume_with_mindee
from firecrawl_engine import FirecrawlSession
from hyperlink import extract_hyperlinks

# --- Configuration ---
MINDEE_API_KEY = "YOUR_MINDEE_KEY"
FIRECRAWL_API_KEY = "fc-YOUR_FIRECRAWL_KEY"

# --- Global State for Clients ---
# We store clients here so they are created only once
resources = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executes on startup and shutdown. 
    Initializes connections once to be reused.
    """
    print("🚀 Starting up: Initializing API Clients...")
    resources["firecrawl"] = FirecrawlSession(FIRECRAWL_API_KEY)
    resources["mindee"] = Client(api_key=MINDEE_API_KEY)
    
    yield  # The application runs here
    
    print("🛑 Shutting down: Cleaning up resources...")
    resources.clear()

app = FastAPI(lifespan=lifespan)

# --- Request Model ---
class ResumeRequest(BaseModel):
    file_path: str  # Path to the PDF on the server

# --- Helper Wrapper for Blocking Code ---
async def run_blocking_task(func, *args):
    """Runs synchronous (blocking) code in a separate thread."""
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func, *args)

# --- The Asynchronous Endpoint ---
@app.post("/process-resume")
async def process_resume(request: ResumeRequest):
    """
    Orchestrates the entire flow:
    1. Extracts links (PyMuPDF)
    2. Parses Resume (Mindee)
    3. Scrapes Links (Firecrawl)
    """
    
    # 1. Validation
    import os
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    print(f"Processing: {request.file_path}")

    # 2. Parallel Execution (Optional Optimization)
    # We can run link extraction and Mindee parsing at the same time
    # since they don't depend on each other.
    
    # Task A: Extract Hyperlinks (CPU bound / Blocking IO)
    # We wrap it because PyMuPDF is synchronous
    links_task = run_blocking_task(extract_hyperlinks, request.file_path)
    
    # Task B: Parse Resume with Mindee (Network bound / Blocking)
    # We wrap it because the standard Mindee client is synchronous
    mindee_task = run_blocking_task(
        parse_resume_with_mindee, 
        request.file_path, 
        resources["mindee"]  # Pass the global client
    )

    # Wait for both A and B to finish
    hyperlinks_data, resume_data = await asyncio.gather(links_task, mindee_task)

    # 3. Scrape the Found Links (Firecrawl)
    scraped_content = []
    
    if hyperlinks_data:
        # Extract just the URL strings from the list of dicts
        url_list = [item['url'] for item in hyperlinks_data]
        
        # FirecrawlSession.scrape_links is likely blocking too (unless you wrote it async),
        # so we wrap it as well to be safe.
        scraped_content = await run_blocking_task(
            resources["firecrawl"].scrape_links, 
            url_list
        )

    # 4. Return Final Combined Response
    return {
        "status": "success",
        "resume_analysis": resume_data,
        "external_links_found": len(hyperlinks_data),
        "scraped_links_content": scraped_content
    }

# --- Standard Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Resume Processing API is Online 🟢"}

# --- Dev Server Entry Point ---
if __name__ == "__main__":
    import uvicorn   #type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)