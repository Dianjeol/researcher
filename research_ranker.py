from dataclasses import dataclass, field
from typing import List, Optional, Set
import asyncio
from search_module import SearchModule
from search_ranker import SearchRanker
import concurrent.futures
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure proper UTF-8 handling
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

@dataclass
class ResearchRequest:
    """
    Request for research containing query and optional parameters
    """
    research_query: str
    search_queries: Set[str] = field(default_factory=set)
    max_results: Optional[int] = None
    test_mode: bool = False

@dataclass
class ResearchResults:
    """
    Results from research containing ranked results
    """
    ranked_results: List[dict]
    total_results: int

class ResearchRanker:
    """
    Research module that integrates multiple search queries and ranks results
    """
    def __init__(self):
        self.searcher = SearchModule()
        self.ranker = SearchRanker()
        
        
    async def _perform_search(self, query: str, test_mode: bool = False) -> List[dict]:
        """Perform a single search asynchronously"""
        try:
            logger.info(f"Searching for query: {query}")
            
            # Using 20 as default per-query limit to get max 120 results (6 queries * 20)
            results = self.searcher.search(query, num_results=20)
            logger.info(f"Raw search results type: {type(results)}")
            logger.info(f"Raw search results: {results}")
            
            if isinstance(results, list):
                return results
            elif isinstance(results, dict) and results.get('error'):
                logger.warning(f"Search error for query '{query}': {results['error']}")
                return []
            elif results is None:
                logger.warning(f"No results for query '{query}'")
                return []
            else:
                try:
                    return list(results)  # Try to convert to list if possible
                except Exception as e:
                    logger.error(f"Could not convert results to list: {e}")
                    return []
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}", exc_info=True)
            return []

    async def _gather_search_results(self, search_queries: List[str], test_mode: bool = False) -> List[dict]:
        """Gather results from multiple searches asynchronously"""
        # Perform searches concurrently
        tasks = [self._perform_search(query, test_mode) for query in search_queries]
        results = await asyncio.gather(*tasks)
        
        # Flatten results and remove duplicates by URL
        seen_urls = set()
        unique_results = []
        
        for result_list in results:
            for result in result_list:
                # Get URL (handle both 'url' and 'link' keys)
                url = result.get('url', result.get('link', ''))
                
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    # Ensure result has all required fields
                    standardized_result = {
                        'url': url,
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'publication_date': result.get('publication_date', result.get('date', ''))
                    }
                    unique_results.append(standardized_result)
        
        logger.info(f"Found {len(unique_results)} unique results")
        return unique_results

    def research(self, request: ResearchRequest) -> ResearchResults:
        """
        Perform research using multiple search queries and rank the results
        Args:
            request: ResearchRequest containing research query, additional search queries, and optional max results
        Returns:
            ResearchResults containing ranked results
        """
        try:
            logger.info(f"Starting research for query: {request.research_query}")
            logger.info(f"Additional queries: {request.search_queries}")
            logger.info(f"Max results: {request.max_results}")
            logger.info(f"Test mode: {request.test_mode}")
            
            # Use only the main query and any user-provided additional queries
            search_queries = [request.research_query] + list(request.search_queries)
            logger.info(f"Using queries: {search_queries}")

            # Run async search gathering in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                search_results = loop.run_until_complete(
                    self._gather_search_results(search_queries, request.test_mode)
                )
            finally:
                loop.close()

            logger.info(f"Total search results gathered: {len(search_results)}")
            if not search_results:
                return ResearchResults(
                    ranked_results=[],
                    total_results=0
                )

            # Rank the results
            logger.info("Ranking results...")
            ranked_results = self.ranker.rank_results(search_results, request.research_query)
            
            # Convert ranked results to a flat list, prioritizing by relevance
            all_results = (
                ranked_results.very_relevant +
                ranked_results.relevant +
                ranked_results.somewhat_relevant +
                ranked_results.not_relevant
            )
            
            # Apply max_results limit if specified
            if request.max_results is not None:
                all_results = all_results[:request.max_results]

            logger.info(f"Final results count: {len(all_results)}")
            return ResearchResults(
                ranked_results=all_results,
                total_results=len(all_results)
            )

        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            return ResearchResults(
                ranked_results=[],
                total_results=0
            )


# Example usage
if __name__ == "__main__":
    researcher = ResearchRanker()
    
    # Get research query
    research_query = input("Enter your research query: ")
    
    # Get additional search queries
    print("\nEnter up to 5 additional search queries (one per line, empty line to finish):")
    search_queries = set()
    for i in range(5):
        query = input(f"{i+1}> ").strip()
        if not query:
            break
        search_queries.add(query)
    
    # Get optional max results
    max_results_str = input("\nEnter maximum number of results (optional, press Enter for no limit): ").strip()
    max_results = int(max_results_str) if max_results_str.isdigit() else None
    
    # Ask about test mode
    test_mode = input("\nUse test mode? (y/N): ").lower().startswith('y')
    
    # Create research request
    request = ResearchRequest(
        research_query=research_query,
        search_queries=search_queries,
        max_results=max_results,
        test_mode=test_mode
    )
    
    # Perform research
    results = researcher.research(request)
    
    # Display results
    if not results.ranked_results:
        print("\nNo results found.")
    else:
        print("\nRESULTS:")
        for i, result in enumerate(results.ranked_results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"URL: {result['url']}")
            print(f"Snippet: {result['snippet'][:200]}...")
            
        print(f"\nTotal results found: {results.total_results}")
