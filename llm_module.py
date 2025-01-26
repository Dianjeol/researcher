import os
from typing import Optional, Dict
from dotenv import load_dotenv
import google.generativeai as genai
import openai
import requests
from dataclasses import dataclass

# Load environment variables
load_dotenv()

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    error: Optional[str] = None

class LLMModule:
    def __init__(self):
        # Initialize API keys
        self.cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

        # Initialize Gemini
        genai.configure(api_key=self.gemini_api_key)
        
        # Initialize OpenAI
        openai.api_key = self.openai_api_key

        # Model mappings
        self.MODEL_CONFIGS = {
            "llama-3.3-70b": {
                "provider": "cerebras",
                "api_url": "https://api.cerebras.ai/v1/completions",
                "headers": {"Authorization": f"Bearer {self.cerebras_api_key}"},
                "model": "llama-3.3-70b"
            },
            "gemini-2.0-flash-exp": {
                "provider": "gemini",
                "model": "gemini-2.0-flash-exp"
            },
            "gemini-exp-1206": {
                "provider": "gemini",
                "model": "gemini-exp-1206"
            },
            "deepseek-chat": {
                "provider": "deepseek",
                "api_url": "https://api.deepseek.com/v1/chat/completions",
                "headers": {"Authorization": f"Bearer {self.deepseek_api_key}"},
                "model": "deepseek-chat"
            },
            "deepseek-reasoner": {
                "provider": "deepseek",
                "api_url": "https://api.deepseek.com/v1/chat/completions",
                "headers": {"Authorization": f"Bearer {self.deepseek_api_key}"},
                "model": "deepseek-reasoner"
            },
            "gpt-4o-mini": {
                "provider": "openai",
                "model": "gpt-4o-mini"
            }
        }

    def _call_cerebras(self, model: str, query: str) -> LLMResponse:
        """Call Cerebras API"""
        try:
            config = self.MODEL_CONFIGS[model]
            response = requests.post(
                config["api_url"],
                headers=config["headers"],
                json={
                    "model": config["model"],
                    "prompt": query,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return LLMResponse(
                content=response.json()["choices"][0]["text"],
                model=model,
                provider="cerebras"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=model,
                provider="cerebras",
                error=str(e)
            )

    def _call_gemini(self, model: str, query: str) -> LLMResponse:
        """Call Gemini API"""
        try:
            config = self.MODEL_CONFIGS[model]
            gemini_model = genai.GenerativeModel(config["model"])
            response = gemini_model.generate_content(query)
            return LLMResponse(
                content=response.text,
                model=model,
                provider="gemini"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=model,
                provider="gemini",
                error=str(e)
            )

    def _call_deepseek(self, model: str, query: str) -> LLMResponse:
        """Call Deepseek API"""
        try:
            config = self.MODEL_CONFIGS[model]
            response = requests.post(
                config["api_url"],
                headers=config["headers"],
                json={
                    "model": config["model"],
                    "messages": [{"role": "user", "content": query}],
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return LLMResponse(
                content=response.json()["choices"][0]["message"]["content"],
                model=model,
                provider="deepseek"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=model,
                provider="deepseek",
                error=str(e)
            )

    def _call_openai(self, model: str, query: str) -> LLMResponse:
        """Call OpenAI API"""
        try:
            config = self.MODEL_CONFIGS[model]
            response = openai.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": query}],
                temperature=0.7
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider="openai"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=model,
                provider="openai",
                error=str(e)
            )

    def query(self, model: str, query: str) -> LLMResponse:
        """
        Query an LLM model with the given text
        Args:
            model: One of "llama-3.3-70b", "gemini-2.0-flash-exp", "gemini-exp-1206",
                  "deepseek-chat", "deepseek-reasoner", "gpt-4o-mini"
            query: The text to send to the model
        Returns:
            LLMResponse object containing the response and metadata
        """
        if model not in self.MODEL_CONFIGS:
            return LLMResponse(
                content="",
                model=model,
                provider="unknown",
                error=f"Unknown model: {model}"
            )

        provider = self.MODEL_CONFIGS[model]["provider"]
        provider_map = {
            "cerebras": self._call_cerebras,
            "gemini": self._call_gemini,
            "deepseek": self._call_deepseek,
            "openai": self._call_openai
        }

        return provider_map[provider](model, query)


# Example usage
if __name__ == "__main__":
    llm = LLMModule()
    
    # Test each model
    test_query = "What is the capital of France?"
    models = [
        "llama-3.3-70b",
        "gemini-2.0-flash-exp",
        "gemini-exp-1206",
        "deepseek-chat",
        "deepseek-reasoner",
        "gpt-4o-mini"
    ]
    
    for model in models:
        print(f"\nTesting {model}:")
        response = llm.query(model, test_query)
        if response.error:
            print(f"Error: {response.error}")
        else:
            print(f"Response: {response.content}")
        print("-" * 80)
