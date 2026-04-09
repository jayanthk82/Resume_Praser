import os
from dotenv import load_dotenv

# Load environment variables from the local .env file (if it exists)
load_dotenv()

def _secret(key: str) -> str:
    """Read from Streamlit secrets first, then OS env."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key)

class Config:
    MINDEE_API_KEY = _secret("MINDEE_API_KEY")
    FIRECRAWL_API_KEY = _secret("FIRECRAWL_API_KEY")
    OPENROUTER_API_KEY = _secret("OPENROUTER_API_KEY")
    HUGGINGFACE_API_KEY = _secret("HUGGINGFACE_API_KEY")