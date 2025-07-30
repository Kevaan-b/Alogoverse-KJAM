import os
#from openai import OpenAI
from abc import ABC, abstractmethod
import anthropic
from anthropic import Anthropic  



class WebSearch(ABC):
    """Abstract base for web search implementations."""
    @abstractmethod
    def search(self, query: str, **tool_kwargs) -> str:
        pass

class AnthropicWebSearch(WebSearch):
    """
    WebSearch implementation for Anthropic
    """

    def __init__(
        self,
        api_key: str = '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',
        model: str = "claude-3-5-sonnet-20241022"
    ):
        # Initialize the Anthropic client
        self.client = Anthropic(api_key=api_key)  
        self.model = model

    def search(
        self,
        query: str,
        max_uses: int = 1,
        allowed_domains: list[str] = None,
        blocked_domains: list[str] = None,
        user_location: dict = None,
        max_tokens: int = 1024,
    ):
       
        tool = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": max_uses,
        }  

        if allowed_domains:
            tool["allowed_domains"] = allowed_domains
        if blocked_domains:
            tool["blocked_domains"] = blocked_domains
        if user_location:
            tool["user_location"] = user_location

        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=[tool],                  
            max_tokens=max_tokens,
        )

        blocks = response.content  # list of dicts
        text_only = [blk.text for blk in blocks if getattr(blk, "type", None) == "text"]

        # 3) Concatenate and display
        result = "\n".join(text_only)
        return result

if __name__ == "__main__":
    # client = Anthropic(api_key="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")
    # response = client.models.list()
    # for model in response.data:
    #     print(model.id, "-", model.display_name)

    searcher = AnthropicWebSearch()
    q = input("Enter search query: ")
    print(searcher.search(
        q,
        max_uses=1,
        allowed_domains=["wikipedia.org"],
    ))
    
