from typing import Dict, Any, Optional, List
from enum import Enum

from src.config import settings


class LLMProvider(Enum):
    GROQ = "groq"


class LLMClient:
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.provider = provider or self._detect_provider()
        self.model = model or self._get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.client = None
        self._initialize_client()
    
    def _detect_provider(self) -> str:
        if settings.GROQ_API_KEY:
            return LLMProvider.GROQ.value
        else:
            raise ValueError("GROQ_API_KEY not found. Only Groq is supported.")
    
    def _get_default_model(self) -> str:
        return settings.GROQ_MODEL or "llama-3.3-70b-versatile"
    
    def _initialize_client(self):
        try:
            if self.provider == LLMProvider.GROQ.value:
                self._initialize_groq()
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            raise
    
    def _initialize_groq(self):
        try:
            from groq import Groq
            
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not found in environment")
            
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        except ImportError:
            raise ImportError(
                "Groq library not installed. "
                "Install with: pip install groq"
            )
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
       
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            return self._generate_groq(prompt, system_prompt, temp, tokens)
        
        except Exception as e:
            raise
    
    def _generate_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "tokens": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            },
            "finish_reason": response.choices[0].finish_reason
        }
    
    def get_client_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
