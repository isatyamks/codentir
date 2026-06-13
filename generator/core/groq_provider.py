import os
from dataclasses import dataclass
from groq import Groq


@dataclass
class GroqResponse:
    content: str


class GroqProvider:
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in environment variables.")
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, messages: list) -> GroqResponse:
        formatted = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            temperature=0.7,
        )
        content = response.choices[0].message.content
        return GroqResponse(content=content)
