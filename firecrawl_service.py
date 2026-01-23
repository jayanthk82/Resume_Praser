from typing import List, Dict, Any
from firecrawl import Firecrawl  #type: ignore

class FirecrawlService:
    def __init__(self, api_key: str):
        """
        Initializes the Firecrawl connection once.
        """
        print("Initializing Firecrawl session...")
        self.app = Firecrawl(api_key=api_key)

    def scrape_links(self, url_list: List[str]) -> List[Dict[str, Any]]:
        """
        Reuses the existing app instance to scrape a list of URLs.
        """
        if not url_list:
            print("No URLs provided for scraping.")
            return []

        print(f"Scraping {len(url_list)} URLs...")

        try:
            # Uses the persistent self.app instance
            batch_result = self.app.batch_scrape_urls(url_list, {
                "formats": ["markdown"],
                "onlyMainContent": True
            })

            if batch_result.get('success'):
                return batch_result.get('data', [])
            else:
                print(f"Batch scrape failed: {batch_result}")
                return []

        except Exception as e:
            print(f"Error during scraping: {e}")
            return []

