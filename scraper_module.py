import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re

@dataclass
class ScrapedContent:
    text: str
    links: List[Dict[str, str]]  # List of dicts with 'text' and 'url' keys
    title: str
    error: Optional[str] = None

class ScraperModule:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Tags to extract text from
        self.text_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'span', 'div']
        # Tags to skip
        self.skip_tags = ['script', 'style', 'noscript', 'header', 'footer', 'nav']
        # Maximum words to return
        self.max_words = 10000

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and newlines"""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _extract_text_and_links(self, soup: BeautifulSoup, base_url: str) -> tuple[str, List[Dict[str, str]]]:
        """Extract text and links from the parsed HTML"""
        text_parts = []
        links = []
        word_count = 0

        # First pass: collect all text and links
        for tag in soup.find_all(True):
            # Skip unwanted tags and their children
            if tag.name in self.skip_tags:
                continue

            # Extract text if it's in our target tags
            if tag.name in self.text_tags:
                text = self._clean_text(tag.get_text())
                if text:
                    current_words = len(text.split())
                    if word_count + current_words <= self.max_words:
                        text_parts.append(text)
                        word_count += current_words
                    else:
                        # Add partial text to reach max_words
                        words = text.split()
                        remaining_words = self.max_words - word_count
                        if remaining_words > 0:
                            text_parts.append(' '.join(words[:remaining_words]))
                        break

            # Extract links
            if tag.name == 'a' and len(links) < 100:  # Limit to 100 links
                href = tag.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    if self._is_valid_url(absolute_url):
                        link_text = self._clean_text(tag.get_text())
                        if link_text:
                            links.append({
                                'text': link_text,
                                'url': absolute_url
                            })

        return ' '.join(text_parts), links

    def scrape(self, url: str) -> ScrapedContent:
        """
        Scrape a webpage and return its text content and links
        Args:
            url: The URL to scrape
        Returns:
            ScrapedContent object containing the text, links, title, and any error
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                return ScrapedContent(
                    text="",
                    links=[],
                    title="",
                    error="Invalid URL provided"
                )

            # Fetch the webpage
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Get title
            title = soup.title.string if soup.title else ""
            title = self._clean_text(title)

            # Extract text and links
            text, links = self._extract_text_and_links(soup, url)

            return ScrapedContent(
                text=text,
                links=links[:10],  # Return only top 10 links
                title=title
            )

        except requests.RequestException as e:
            return ScrapedContent(
                text="",
                links=[],
                title="",
                error=f"Failed to fetch URL: {str(e)}"
            )
        except Exception as e:
            return ScrapedContent(
                text="",
                links=[],
                title="",
                error=f"Error scraping content: {str(e)}"
            )


# Example usage
if __name__ == "__main__":
    scraper = ScraperModule()
    
    # Test URL
    test_url = input("Enter a URL to scrape: ")
    result = scraper.scrape(test_url)
    
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"\nTitle: {result.title}")
        print("\nText preview (first 500 characters):")
        print(result.text[:500] + "...")
        print(f"\nTotal words: {len(result.text.split())}")
        
        print("\nTop 10 links found:")
        for i, link in enumerate(result.links, 1):
            print(f"{i}. {link['text']}: {link['url']}")
