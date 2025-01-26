import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from typing import List, Dict

# Load environment variables
load_dotenv()

class SearchModule:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        # Initialize Google Search API
        self.google_service = build(
            "customsearch", "v1",
            developerKey=self.google_api_key
        )

    def search(self, query: str, num_results: int = 20) -> List[Dict]:
        """
        Perform a Google search using Custom Search API
        Returns up to 20 results
        """
        try:
            results = []
            # Google Custom Search API can only return max 10 results per request
            for i in range(0, min(num_results, 20), 10):
                response = self.google_service.cse().list(
                    q=query,
                    cx=self.search_engine_id,
                    start=i + 1,
                    num=min(10, num_results - i)
                ).execute()
                
                if 'items' in response:
                    for item in response['items']:
                        results.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', '')
                        })
            return results
        except Exception as e:
            print(f"Error in Google search: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    search_module = SearchModule()
    
    # Test search
    query = input("Enter your search query: ")
    results = search_module.search(query)
    
    print(f"\nFound {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}.")
        print(f"Title: {result['title']}")
        print(f"Link: {result['link']}")
        print(f"Description: {result['snippet']}")
        if result['date']:
            print(f"Date: {result['date']}")
        print("-" * 80 + "\n")
