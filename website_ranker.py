from dataclasses import dataclass
from typing import List, Optional
from llm_module import LLMModule
from analyzer_module import AnalysisResult
import logging

logger = logging.getLogger(__name__)

@dataclass
class RankedWebsite:
    """A website that has been analyzed and ranked"""
    title: str
    url: str
    summary: str
    importance: str  # e.g. "very important", "important", "somewhat important"
    relevance: str  # e.g. "very relevant", "relevant", "somewhat relevant"
    next_actions: List[str]
    error: Optional[str] = None

class WebsiteRanker:
    """
    Ranks analyzed websites based on their importance to the research query.
    Uses LLM to evaluate importance and adjust relevance categories.
    """
    def __init__(self):
        self.llm = LLMModule()

    def rank_websites(self, research_query: str, analyzed_results: List[AnalysisResult]) -> List[RankedWebsite]:
        """
        Ranks the analyzed websites based on their importance to the research query.
        
        Args:
            research_query: The main research question/objective
            analyzed_results: List of analyzed website content
            
        Returns:
            List of ranked websites with importance ratings and next actions
        """
        ranked_websites = []
        
        for result in analyzed_results:
            try:
                # Evaluate importance and next actions using LLM
                importance_prompt = f"""
                Research Query: {research_query}
                
                Website Content Summary:
                Title: {result.title}
                Summary: {result.summary}
                
                Evaluate how important this website is for answering the research query.
                Rate it as one of: "very important", "important", "somewhat important", "not important"
                Also suggest 2-3 specific next actions based on this content.
                
                Format:
                Importance: [rating]
                Next Actions:
                - [action 1]
                - [action 2]
                - [action 3]
                """
                
                evaluation = self.llm.generate_text(importance_prompt)
                
                # Parse evaluation
                importance = "somewhat important"  # default
                next_actions = []
                
                for line in evaluation.split('\n'):
                    if line.startswith('Importance:'):
                        importance = line.split(':')[1].strip().lower()
                    elif line.startswith('-'):
                        next_actions.append(line[1:].strip())
                
                ranked_website = RankedWebsite(
                    title=result.title,
                    url=result.url,
                    summary=result.summary,
                    importance=importance,
                    relevance=result.relevance,
                    next_actions=next_actions
                )
                
                ranked_websites.append(ranked_website)
                
            except Exception as e:
                logger.error(f"Error ranking website {result.url}: {str(e)}")
                ranked_website = RankedWebsite(
                    title=result.title,
                    url=result.url,
                    summary=result.summary,
                    importance="unknown",
                    relevance=result.relevance,
                    next_actions=[],
                    error=str(e)
                )
                ranked_websites.append(ranked_website)
        
        # Sort by importance (very important > important > somewhat important)
        importance_order = {
            "very important": 0,
            "important": 1,
            "somewhat important": 2,
            "not important": 3,
            "unknown": 4
        }
        
        ranked_websites.sort(key=lambda x: importance_order.get(x.importance, 5))
        
        return ranked_websites
