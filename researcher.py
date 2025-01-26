from dataclasses import dataclass
from typing import List, Optional, Set
import logging
from research_ranker import ResearchRanker, ResearchRequest, ResearchResults
from search_ranker import RankedResult, SearchRanker
from analyzer_module import ContentAnalyzer, AnalysisResult
from scraper_module import ScraperModule, ScrapedContent
from llm_module import LLMModule
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure proper UTF-8 handling
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

@dataclass
class ResearcherRequest:
    """Request for the researcher containing queries"""
    research_query: str  # The main research objective/question
    initial_query: str   # The initial search query from user

@dataclass
class ResearcherResults:
    """Results from the researcher containing search results and analysis"""
    search_results: List[RankedResult]  # All search results
    analyzed_results: List[AnalysisResult]  # Analyzed content from selected URLs
    total_results: int
    queries_used: Set[str]  # All queries that were used
    error: Optional[str] = None

class Researcher:
    """
    Orchestrates the research process by:
    1. Generating additional search queries if needed
    2. Using ResultRanker to get ranked results
    3. Analyzing the most relevant results in detail
    """
    def __init__(self):
        self.llm = LLMModule()
        self.ranker = SearchRanker()
        self.analyzer = ContentAnalyzer()
        self.scraper = ScraperModule()

    def _generate_search_queries(self, research_query: str, initial_query: str) -> Set[str]:
        """
        Generate additional search queries based on the research objective
        """
        try:
            logger.info(f"Generating search queries for research: {research_query}")
            
            prompt = f"""
            RESEARCH OBJECTIVE: {research_query}
            INITIAL QUERY: {initial_query}

            Generate 4 additional search queries that would help find information about this research objective.
            The queries should:
            1. Cover different aspects or angles of the research objective
            2. Use different phrasings and synonyms
            3. Be specific and targeted
            4. Be in German since this is for Berlin

            Format each query in quotes, one per line.
            """
            
            response = self.llm.query(
                "gemini-2.0-flash-exp",
                prompt
            ).content
            
            # Extract queries (anything in quotes)
            import re
            queries = set(re.findall(r'"([^"]*)"', response))
            queries.add(initial_query)  # Add the initial query
            
            logger.info(f"Generated queries: {queries}")
            return queries
            
        except Exception as e:
            logger.error(f"Error generating queries: {str(e)}", exc_info=True)
            return {initial_query}  # Return just the initial query on error

    def _select_urls_to_analyze(self, search_results: List[RankedResult], research_query: str) -> List[str]:
        """
        Select which URLs to analyze in detail based on their relevance
        """
        try:
            # Format results for LLM prompt
            results_text = "\n".join([
                f"{i+1}. {r.title}\n   URL: {r.url}\n   Snippet: {r.snippet}"
                for i, r in enumerate(search_results)
            ])
            
            # For now, just analyze the top 3 results
            return [r.url for r in search_results[:3]]
            
        except Exception as e:
            logger.error(f"Error selecting URLs: {str(e)}", exc_info=True)
            # Return empty list on error
            return []


    def research(self, request: ResearcherRequest) -> ResearcherResults:
        """
        Perform comprehensive research based on the request
        """
        try:
            # Step 1: Generate search queries
            logger.info(f"Generating search queries for research: {request.research_query}")
            search_queries = self._generate_search_queries(
                request.research_query,
                request.initial_query
            )
            
            # Step 2: Get ranked search results
            logger.info("Getting ranked search results")
            
            research_ranker = ResearchRanker()
            research_request = ResearchRequest(
                research_query=request.research_query,
                search_queries=search_queries
            )
            research_results = research_ranker.research(research_request)
            
            if not research_results.ranked_results:
                return ResearcherResults(
                    search_results=[],
                    analyzed_results=[],
                    total_results=0,
                    queries_used=search_queries,
                    error="No relevant search results found"
                )
            
            all_results = research_results.ranked_results

            # Step 3: Select URLs to analyze
            urls_to_analyze = self._select_urls_to_analyze(
                all_results,
                request.research_query
            )
            
            # Step 4: Analyze selected URLs
            logger.info(f"Analyzing {len(urls_to_analyze)} URLs")
            analyzed_results = []
            for url in urls_to_analyze:
                try:
                    scraped_content = self.scraper.scrape(url)
                    if not scraped_content.error:
                        # Analyze content
                        analysis = self.analyzer.analyze_content(
                            scraped_content,
                            request.research_query
                        )
                        analyzed_results.append(analysis)
                except Exception as e:
                    logger.error(f"Error analyzing {url}: {str(e)}", exc_info=True)
                    continue

            return ResearcherResults(
                search_results=all_results,
                analyzed_results=analyzed_results,
                total_results=len(all_results),
                queries_used=search_queries
            )

        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ResearcherResults(
                search_results=[],
                analyzed_results=[],
                total_results=0,
                queries_used=set(),
                error=error_msg
            )


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    researcher = Researcher()
    
    # Get research query
    research_query = input("Enter your research objective/question: ")
    initial_query = input("Enter your initial search query: ")
    
    # Perform research
    results = researcher.research(ResearcherRequest(
        research_query=research_query,
        initial_query=initial_query
    ))
    
    # Display results
    if results.error:
        print(f"\nError: {results.error}")
    else:
        print("\nQUERIES USED:")
        for query in results.queries_used:
            print(f"- {query}")
            
        print(f"\nTOTAL SEARCH RESULTS: {results.total_results}")
        
        print("\nTOP SEARCH RESULTS:")
        for i, result in enumerate(results.search_results[:10], 1):
            print(f"\n{i}. {result.title}")
            print(f"URL: {result.url}")
            print(f"Snippet: {result.snippet[:200]}...")
            
        print("\nDETAILED ANALYSES:")
        for i, analysis in enumerate(results.analyzed_results, 1):
            print(f"\nANALYSIS {i}:")
            print(f"Title: {analysis.title}")
            print(f"URL: {analysis.url}")
            print(f"Summary: {analysis.summary}")
            print(f"Relevance: {analysis.relevance_rating}")
            print(f"Explanation: {analysis.relevance_explanation}")
            print("\nNext Actions:")
            for action in analysis.next_actions:
                print(f"- {action}")
            
            if analysis.contact_info.emails or analysis.contact_info.phones or \
               analysis.contact_info.social_media or analysis.contact_info.addresses:
                print("\nContact Information:")
                if analysis.contact_info.emails:
                    print("Emails:", ", ".join(analysis.contact_info.emails))
                if analysis.contact_info.phones:
                    print("Phones:", ", ".join(analysis.contact_info.phones))
                if analysis.contact_info.social_media:
                    print("Social Media:", ", ".join(analysis.contact_info.social_media))
                if analysis.contact_info.addresses:
                    print("Addresses:", ", ".join(analysis.contact_info.addresses))
