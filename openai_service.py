"""
OpenAI service for API interactions with robust error handling and retry logic.
"""

import asyncio
import logging
from typing import List, Dict, Union, Optional, Any  # Added Any import
from datetime import datetime
import backoff

from openai import OpenAI, AsyncOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .config import Config

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for OpenAI API interactions with retry logic and error handling."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
            timeout=Config.TIMEOUT_SECONDS
        )
        self.async_client = AsyncOpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
            timeout=Config.TIMEOUT_SECONDS
        )
        
        # Rate limiting and metrics
        self.request_count = 0
        self.total_tokens = 0
        self.error_count = 0
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=Config.RETRY_ATTEMPTS,
        factor=2
    )
    async def get_embeddings(self, texts: List[str], model: str = None) -> List[List[float]]:
        """Generate embeddings using OpenAI's embedding model."""
        if model is None:
            model = Config.EMBEDDING_MODEL
        
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            
            response = await self.async_client.embeddings.create(
                model=model,
                input=texts,
                encoding_format="float"
            )
            
            self.request_count += 1
            embeddings = [data.embedding for data in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=Config.RETRY_ATTEMPTS,
        factor=2
    )
    async def chat_completion(self, messages: List[Union[Dict[str, str], SystemMessage, HumanMessage, AIMessage]], 
                            model: str = None, **kwargs) -> str:
        """Generate chat completion using OpenAI's API."""
        if model is None:
            model = Config.CHAT_MODEL
        
        try:
            # Convert LangChain messages to dict format for OpenAI API
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)):
                    if isinstance(msg, SystemMessage):
                        formatted_messages.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        formatted_messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        formatted_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, dict):
                    formatted_messages.append(msg)
                else:
                    formatted_messages.append({"role": "user", "content": str(msg)})
            
            logger.debug(f"Chat completion request with {len(formatted_messages)} messages")
            
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                **kwargs
            )
            
            self.request_count += 1
            if response.usage:
                self.total_tokens += response.usage.total_tokens
            
            content = response.choices[0].message.content
            logger.debug(f"Chat completion response: {len(content)} characters")
            
            return content
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error in chat completion: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:  # Fixed Any usage
        """Get API usage statistics."""
        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1)
        }
    
    def reset_statistics(self):
        """Reset API usage statistics."""
        self.request_count = 0
        self.total_tokens = 0
        self.error_count = 0

# Global OpenAI service instance
openai_service = None

async def initialize_openai_service() -> OpenAIService:
    """Initialize the global OpenAI service."""
    global openai_service
    openai_service = OpenAIService()
    logger.info("OpenAI service initialized successfully")
    return openai_service

def get_openai_service() -> OpenAIService:
    """Get the global OpenAI service instance."""
    return openai_service