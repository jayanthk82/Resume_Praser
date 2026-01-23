from typing import List, Dict, Any
from firecrawl import Firecrawl  #type: ignore


from typing import List, Dict, Any


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
        scrape_result = list()
        for url in url_list:
            try:
                job = self.app.crawl(url, limit=5, poll_interval=1, timeout=120)
                #result = filter_firecrawl_data(job)
                scrape_result.append(job)
            except Exception as e:
                continue 
        if scrape_result:
            return scrape_result
        else:
            print(f"Batch scrape failed: {scrape_result}")
            return []
