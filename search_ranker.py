from dataclasses import dataclass
from typing import List, Optional, Dict
from llm_module import LLMModule
import re
from operator import attrgetter
import logging

logger = logging.getLogger(__name__)

@dataclass
class RankedResult:
    url: str
    title: str
    snippet: str
    relevance_rating: str  # Very relevant, relevant, somewhat relevant, not relevant
    relevance_explanation: str
    rank_score: float  # Higher is better, used for sorting within categories
    publication_date: Optional[str] = None

@dataclass
class RankingResults:
    very_relevant: List[RankedResult]
    relevant: List[RankedResult]
    somewhat_relevant: List[RankedResult]
    not_relevant: List[RankedResult]
    error: Optional[str] = None

class SearchRanker:
    def __init__(self):
        self.llm = LLMModule()
        
    def _calculate_rank_score(self, result: Dict) -> float:
        """
        Calculate a numerical score for ranking within categories.
        Higher score means higher rank.
        """
        score = 0.0
        
        # Factor 1: Recency (if available)
        if result.get('publication_date'):
            score += 1.0
            
        # Factor 2: Title relevance (presence of query terms)
        if result.get('title'):
            score += 0.5
            
        # Factor 3: Snippet length and quality
        if result.get('snippet'):
            desc_length = len(result['snippet'])
            score += min(desc_length / 1000, 1.0)  # Cap at 1.0
            
        return score

    def rank_results(self, search_results: List[Dict], query: str) -> RankingResults:
        """
        Rank search results based on their potential relevance to the query
        Args:
            search_results: List of dictionaries, each containing at least 'url', 'title', and 'snippet'
            query: The research query to evaluate relevance against
        Returns:
            RankingResults object containing sorted lists of results by relevance category
        """
        try:
            if not search_results:
                return RankingResults([], [], [], [], "No search results provided")
            
            # Prepare prompt for batch analysis
            analysis_prompt = f"""
            RESEARCH QUERY: {query}

            Analyze each search result below and rate its potential relevance for answering the query.
            Rate each result as exactly one of: Very relevant, relevant, somewhat relevant, not relevant
            Also provide a brief explanation (max 50 words) for each rating.

            For each result, format your response exactly as:
            [NUMBER]. RATING: [your rating]
            EXPLANATION: [your explanation]

            SEARCH RESULTS:
            """
            
            # Add each result to the prompt
            for i, result in enumerate(search_results, 1):
                analysis_prompt += f"""
                {i}. TITLE: {result.get('title', 'No title')}
                SNIPPET: {result.get('snippet', 'No description available')}
                URL: {result.get('url', 'No URL')}
                """
            
            # Get LLM analysis
            models = [
                "deepseek-reasoner",
                "gemini-2.0-flash-exp",
                "cerebras-2.0-flash",
                "deepseek-chat",
                "gpt-4-mini"
            ]

            last_error = None
            analysis = None
            
            for model in models:
                try:
                    print(f"Trying model: {model}")
                    analysis = self.llm.query(
                        model=model,
                        query=analysis_prompt
                    ).content
                    break  # If we get here, the model worked
                except Exception as e:
                    last_error = e
                    print(f"Warning: {model} failed ({str(e)}), trying next model")
                    continue
            
            if analysis is None:
                return RankingResults([], [], [], [], f"All models failed. Last error: {str(last_error)}")
            
            # Parse LLM response and create RankedResults
            very_relevant = []
            relevant = []
            somewhat_relevant = []
            not_relevant = []
            
            # Extract ratings using regex
            result_pattern = r'(\d+)\. RATING: (.*?)\nEXPLANATION: (.*?)(?=\n\d+\.|$)'
            matches = re.finditer(result_pattern, analysis, re.DOTALL)
            
            for match in matches:
                index = int(match.group(1)) - 1  # Convert to 0-based index
                if index < len(search_results):
                    result = search_results[index]
                    rating = match.group(2).strip()
                    explanation = match.group(3).strip()
                    
                    ranked_result = RankedResult(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        snippet=result.get('snippet', ''),
                        relevance_rating=rating,
                        relevance_explanation=explanation,
                        rank_score=self._calculate_rank_score(result),
                        publication_date=result.get('publication_date')
                    )
                    
                    # Add to appropriate category
                    if rating.lower() == "very relevant":
                        very_relevant.append(ranked_result)
                    elif rating.lower() == "relevant":
                        relevant.append(ranked_result)
                    elif rating.lower() == "somewhat relevant":
                        somewhat_relevant.append(ranked_result)
                    else:
                        not_relevant.append(ranked_result)
            
            # Sort within categories by rank_score
            very_relevant.sort(key=attrgetter('rank_score'), reverse=True)
            relevant.sort(key=attrgetter('rank_score'), reverse=True)
            somewhat_relevant.sort(key=attrgetter('rank_score'), reverse=True)
            not_relevant.sort(key=attrgetter('rank_score'), reverse=True)
            
            return RankingResults(
                very_relevant=very_relevant,
                relevant=relevant,
                somewhat_relevant=somewhat_relevant,
                not_relevant=not_relevant
            )
            
        except Exception as e:
            return RankingResults([], [], [], [], str(e))


# Example usage
if __name__ == "__main__":
    # Create some test search results
    test_results = [
        {
            'url': 'https://example.com/udhr/preamble',
            'title': 'The Universal Declaration of Human Rights: Understanding the Preamble',
            'snippet': 'The preamble of the UDHR begins with recognition of the inherent dignity and equal rights of all members of the human family as the foundation of freedom, justice, and peace in the world...',
            'publication_date': '2024-01-26'
        },
        {
            'url': 'https://example.com/udhr/history',
            'title': 'Historical Context of Human Rights Declaration',
            'snippet': 'Following the devastating events of World War II, the international community came together to draft a revolutionary document that would affirm the dignity and worth of every human being...',
            'publication_date': '2024-01-25'
        },
        {
            'url': 'https://example.com/udhr/impact',
            'title': 'How the UDHR Preamble Shapes Modern Human Rights',
            'snippet': 'The preamble\'s emphasis on human dignity and equality continues to influence constitutions, laws, and human rights movements worldwide. Its vision of universal rights transcends national boundaries...',
            'publication_date': '2024-01-24'
        },
        {
            'url': 'https://example.com/udhr/education',
            'title': 'Teaching Human Rights: Starting with the Preamble',
            'snippet': 'Educators worldwide use the UDHR preamble as a powerful tool to introduce students to fundamental human rights concepts. Its clear language about human dignity resonates across cultures...',
            'publication_date': '2024-01-23'
        }
    ]
    
    ranker = SearchRanker()
    
    # Get query from user
    query = input("Enter your research query: ")
    
    # Rank the test results
    results = ranker.rank_results(test_results, query)
    
    if results.error:
        print(f"\nError: {results.error}")
    else:
        print("\nVERY RELEVANT RESULTS:")
        for i, result in enumerate(results.very_relevant, 1):
            print(f"\n{i}. {result.title}")
            print(f"URL: {result.url}")
            print(f"Score: {result.rank_score:.2f}")
            print(f"Explanation: {result.relevance_explanation}")
            print(f"Snippet: {result.snippet[:200]}...")
            
        print("\nRELEVANT RESULTS:")
        for i, result in enumerate(results.relevant, 1):
            print(f"\n{i}. {result.title}")
            print(f"URL: {result.url}")
            print(f"Score: {result.rank_score:.2f}")
            print(f"Explanation: {result.relevance_explanation}")
            print(f"Snippet: {result.snippet[:200]}...")
            
        if not results.very_relevant and not results.relevant:
            print("\nNo highly relevant results found.")
            
        print(f"\nTotal results found:")
        print(f"Very relevant: {len(results.very_relevant)}")
        print(f"Relevant: {len(results.relevant)}")
        print(f"Somewhat relevant: {len(results.somewhat_relevant)}")
        print(f"Not relevant: {len(results.not_relevant)}")
