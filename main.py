import logging
from researcher import Researcher, ResearcherRequest, ResearcherResults
import sys
from llm_module import LLMModule

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure proper UTF-8 handling
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    """
    Main function to orchestrate the research process
    """
    try:
        # Get initial user prompt
        initial_query = input("Enter your initial research query: ")
        
        # Initialize LLM module
        llm = LLMModule()
        
        # Generate research query suggestions
        prompt = f"""
        INITIAL QUERY: {initial_query}
        
        Based on the initial query, suggest 3 different research queries that would help find information about this topic.
        The queries should:
        1. Cover different aspects or angles of the initial query
        2. Use different phrasings and synonyms
        3. Be specific and targeted
        
        Format each query in quotes, one per line.
        """
        
        response = llm.query(
            "gemini-2.0-flash-exp",
            prompt
        ).content
        
        # Extract queries (anything in quotes)
        import re
        suggested_queries = re.findall(r'"([^"]*)"', response)
        
        # Present options to user
        print("\nSuggested research queries:")
        for i, query in enumerate(suggested_queries, 1):
            print(f"{i}. {query}")
        
        while True:
            choice = input("\nSelect a query number or enter your own: ")
            if choice.isdigit() and 1 <= int(choice) <= len(suggested_queries):
                research_query = suggested_queries[int(choice) - 1]
                break
            else:
                research_query = choice
                break
        
        # Initialize researcher
        researcher = Researcher()
        
        # Perform research
        research_request = ResearcherRequest(
            research_query=research_query,
            initial_query=initial_query
        )
        
        results = researcher.research(research_request)
        
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
    
    except Exception as e:
        logger.error(f"Main function failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
