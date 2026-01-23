import os
from dotenv import load_dotenv #type: ignore

load_dotenv()
class Config:
    # Use environment variables or fallback to placeholders
    MINDEE_API_KEY = os.getenv("MINDEE_API_KEY")
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
