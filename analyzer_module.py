from dataclasses import dataclass
from typing import List, Optional
from scraper_module import ScrapedContent
from llm_module import LLMModule
import re

@dataclass
class ContactInfo:
    emails: List[str]
    phones: List[str]
    social_media: List[str]
    addresses: List[str]

@dataclass
class AnalysisResult:
    url: str
    title: str
    summary: str
    relevance_rating: str  # Very relevant, relevant, somewhat relevant, not relevant
    relevance_explanation: str
    contact_info: ContactInfo
    next_actions: List[str]
    error: Optional[str] = None

class ContentAnalyzer:
    def __init__(self):
        self.llm = LLMModule()
        # Regex patterns for contact information
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        self.social_media_pattern = r'(?:https?://)?(?:www\.)?(?:facebook|twitter|linkedin|instagram)\.com/[\w\.-]+'
        
    def _extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information from text using regex patterns"""
        emails = list(set(re.findall(self.email_pattern, text)))
        phones = list(set(re.findall(self.phone_pattern, text)))
        social_media = list(set(re.findall(self.social_media_pattern, text)))
        
        # Use LLM to identify addresses
        address_prompt = """
        Extract physical addresses from the following text. Return ONLY the addresses, one per line.
        If no addresses are found, return 'None found'.
        
        TEXT:
        {text}
        """
        
        address_response = self.llm.query(
            model="gemini-2.0-flash-exp",
            query=address_prompt.format(text=text[:2000])  # Limit text length for address extraction
        ).content
        
        addresses = [addr.strip() for addr in address_response.split('\n') if addr.strip() and addr.strip().lower() != 'none found']
        
        return ContactInfo(
            emails=emails[:5],  # Limit to top 5 of each
            phones=phones[:5],
            social_media=social_media[:5],
            addresses=addresses[:5]
        )

    def _parse_analysis(self, analysis: str, scraped_content: ScrapedContent) -> AnalysisResult:
        # Parse LLM response
        try:
            # Extract sections using regex
            summary_match = re.search(r'SUMMARY:\s*(.*?)\s*RELEVANCE:', analysis, re.DOTALL)
            relevance_match = re.search(r'RELEVANCE:\s*(.*?)\s*RELEVANCE EXPLANATION:', analysis, re.DOTALL)
            explanation_match = re.search(r'RELEVANCE EXPLANATION:\s*(.*?)\s*NEXT ACTIONS:', analysis, re.DOTALL)
            actions_match = re.search(r'NEXT ACTIONS:\s*(.*?)$', analysis, re.DOTALL)

            summary = summary_match.group(1).strip() if summary_match else ""
            relevance = relevance_match.group(1).strip() if relevance_match else "not relevant"
            explanation = explanation_match.group(1).strip() if explanation_match else ""
            actions_text = actions_match.group(1).strip() if actions_match else ""
            
            # Parse actions list
            next_actions = [
                action.strip('- ').strip()
                for action in actions_text.split('\n')
                if action.strip('- ').strip()
            ]

            # Extract contact information
            contact_info = self._extract_contact_info(scraped_content.text)

            return AnalysisResult(
                url=scraped_content.url if hasattr(scraped_content, 'url') else "",
                title=scraped_content.title,
                summary=summary,
                relevance_rating=relevance,
                relevance_explanation=explanation,
                contact_info=contact_info,
                next_actions=next_actions
            )

        except Exception as e:
            return AnalysisResult(
                url=scraped_content.url if hasattr(scraped_content, 'url') else "",
                title=scraped_content.title,
                summary="",
                relevance_rating="not relevant",
                relevance_explanation="Error analyzing content",
                contact_info=ContactInfo([], [], [], []),
                next_actions=[],
                error=str(e)
            )

    def analyze_content(self, scraped_content: ScrapedContent, research_query: str) -> AnalysisResult:
        """
        Analyze scraped content against a research query
        """
        if scraped_content.error:
            return AnalysisResult(
                url="",
                title="",
                summary="",
                relevance_rating="not relevant",
                relevance_explanation="Error accessing content",
                contact_info=ContactInfo([], [], [], []),
                next_actions=[],
                error=scraped_content.error
            )

        try:
            # Create analysis prompt
            analysis_prompt = f"""
            RESEARCH QUERY: {research_query}

            WEBSITE CONTENT:
            Title: {scraped_content.title}
            Content: {scraped_content.text}

            Analyze this website content in relation to the research query. Provide:

            1. A concise summary (max 200 words)
            2. Relevance rating (MUST be exactly one of: Very relevant, relevant, somewhat relevant, not relevant)
            3. Brief explanation of the relevance rating (max 100 words)
            4. List of recommended next actions based on the content and query (max 5 items)

            Format your response exactly as follows:
            SUMMARY:
            [your summary]

            RELEVANCE:
            [your rating]

            RELEVANCE EXPLANATION:
            [your explanation]

            NEXT ACTIONS:
            - [action 1]
            - [action 2]
            etc.
            """

            # Try models in sequence
            models = [
                "gemini-2.0-flash-exp",
                "cerebras-2.0-flash",
                "deepseek-chat",
                "gpt-4-mini"
            ]

            last_error = None
            for model in models:
                try:
                    print(f"Trying model: {model}")
                    analysis = self.llm.query(
                        model=model,
                        query=analysis_prompt
                    ).content
                    
                    # If we get here, the model worked
                    return self._parse_analysis(analysis, scraped_content)
                    
                except Exception as e:
                    last_error = e
                    print(f"Warning: {model} failed ({str(e)}), trying next model")
                    continue
            
            # If we get here, all models failed
            raise Exception(f"All models failed. Last error: {str(last_error)}")

        except Exception as e:
            return AnalysisResult(
                url=scraped_content.url if hasattr(scraped_content, 'url') else "",
                title=scraped_content.title,
                summary="Error analyzing content",
                relevance_rating="not relevant",
                relevance_explanation=f"Error: {str(e)}",
                contact_info=ContactInfo([], [], [], []),
                next_actions=["Try analysis again", "Check model availability"],
                error=str(e)
            )


# Example usage
if __name__ == "__main__":
    from scraper_module import ScraperModule
    
    # Get URL and query from user
    url = input("Enter a URL to analyze: ")
    query = input("Enter your research query: ")
    
    # Scrape the content
    scraper = ScraperModule()
    scraped_content = scraper.scrape(url)
    
    # Analyze the content
    analyzer = ContentAnalyzer()
    result = analyzer.analyze_content(scraped_content, query)
    
    # Print results
    if result.error:
        print(f"\nError: {result.error}")
    else:
        print(f"\nTitle: {result.title}")
        print(f"\nTotal words in scraped content: {len(scraped_content.text.split())}")
        print(f"\nSummary: {result.summary}")
        print(f"\nRelevance Rating: {result.relevance_rating}")
        print(f"\nRelevance Explanation: {result.relevance_explanation}")
        
        print("\nContact Information:")
        if result.contact_info.emails:
            print("Emails:", ", ".join(result.contact_info.emails))
        if result.contact_info.phones:
            print("Phones:", ", ".join(result.contact_info.phones))
        if result.contact_info.social_media:
            print("Social Media:", ", ".join(result.contact_info.social_media))
        if result.contact_info.addresses:
            print("Addresses:", "\n".join(result.contact_info.addresses))
            
        print("\nRecommended Next Actions:")
        for i, action in enumerate(result.next_actions, 1):
            print(f"{i}. {action}")
