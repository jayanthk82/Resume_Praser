import os
from typing import List, Dict, Any
from firecrawl import FirecrawlApp #type: ignore

class FirecrawlSession:
    def __init__(self, api_key: str):
        """
        Initializes the Firecrawl connection once.
        """
        print("Initializing Firecrawl session...")
        self.app = FirecrawlApp(api_key=api_key)

    def scrape_links(self, url_list: List[str]) -> List[Dict[str, Any]]:
        """
        Reuses the existing app instance to scrape a list of URLs.
        """
        if not url_list:
            print("No URLs provided.")
            return []

        print(f"Scraping {len(url_list)} URLs...")

        try:
            # Uses the persistent self.app instance
            batch_result = self.app.batch_scrape_urls(url_list, {
                "formats": ["markdown"],
                "onlyMainContent": True
            })

            if batch_result['success']:
                return batch_result['data']
            else:
                print(f"Batch scrape failed: {batch_result}")
                return []

        except Exception as e:
            print(f"Error during scraping: {e}")
            return []