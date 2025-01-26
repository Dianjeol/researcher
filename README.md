# Research Assistant 🔍

A powerful research assistant that helps gather, analyze, and summarize information from multiple sources. Built with Python and powered by advanced language models.

## Features ✨

- **Intelligent Query Generation**: Automatically generates focused search queries based on your research objective
- **Smart Result Ranking**: Ranks search results by relevance using an advanced website ranker
- **Deep Content Analysis**: Analyzes webpage content to extract key information and assess relevance
- **Comprehensive Summaries**: Provides detailed summaries and actionable next steps
- **Multi-language Support**: Currently optimized for English and German
- **Efficient URL Selection**: Intelligently selects the most relevant URLs for detailed analysis
- **Integrated Website Ranking**: Ranks analyzed websites based on their importance to your research query

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/Dianjeol/researcher.git
cd researcher
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your API keys:
```bash
GOOGLE_SEARCH_API_KEY=your_api_key
GOOGLE_SEARCH_CX=your_cx_id
GEMINI_API_KEY=your_gemini_api_key
```

## Usage 💡

```python
from researcher import ResearcherModule, ResearcherRequest

# Initialize the researcher
researcher = ResearcherModule()

# Create a research request
request = ResearcherRequest(
    research_query="What are the latest developments in quantum computing?",
    initial_query="quantum computing breakthroughs 2025"
)

# Perform research
results = researcher.research(request)

# Print results
print("\nQUERIES USED:")
for query in results.queries_used:
    print(f"- {query}")

print("\nTOP RANKED RESULTS:")
for result in results.ranked_results[:5]:
    print(f"\n{result.title}")
    print(f"URL: {result.url}")
    print(f"Relevance: {result.relevance}")
    print(f"Snippet: {result.snippet[:200]}...")

print("\nDETAILED ANALYSES:")
for analysis in results.analyzed_results:
    print(f"\nANALYSIS:")
    print(f"Title: {analysis.title}")
    print(f"Summary: {analysis.summary}")
    print(f"Importance: {analysis.importance}")
    print(f"Next Actions:")
    for action in analysis.next_actions:
        print(f"- {action}")
```

## Architecture 🏗️

The system consists of several key modules:

- **ResearcherModule**: Main orchestrator that coordinates the research process
- **WebsiteRanker**: Ranks websites based on their importance to the research query
- **SearchRanker**: Ranks initial search results based on relevance
- **ScraperModule**: Extracts content from web pages
- **AnalyzerModule**: Analyzes and summarizes webpage content
- **LLMModule**: Handles interactions with language models for various tasks

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Thanks to Google for providing the Search and Gemini APIs
- Thanks to all contributors who have helped improve this project

## Contact 📧

Project Link: [https://github.com/Dianjeol/researcher](https://github.com/Dianjeol/researcher)

---
Made with ❤️ by [Dianjeol](https://github.com/Dianjeol)
