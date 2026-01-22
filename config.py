import os

class Config:
    # Use environment variables or fallback to placeholders
    MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "md_rSSY4sX-Tullrv-aHUPeQTRx_YvW0PWzlTQ37lwqRqY")
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "fc-eb709e4a991a45b78dfda6156dc306e6")