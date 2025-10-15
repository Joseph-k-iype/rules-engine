"""
OpenAI API service for the legislation rules converter.
Location: src/services/openai_service.py
"""
import logging
from typing import List, Union, Dict, Optional, Any
from openai import OpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..config import Config

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions."""

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings."""
        try:
            response = self.client.embeddings.create(
                model=Config.EMBEDDING_MODEL,
                input=texts,
                encoding_format="float"
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def chat_completion(self, messages: List[Union[Dict[str, str], SystemMessage, HumanMessage, AIMessage]]) -> str:
        """
        Generate chat completion with default settings.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            String response from the model
        """
        try:
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

            response = self.client.chat.completions.create(
                model=Config.CHAT_MODEL,
                messages=formatted_messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise

    async def get_completion(
        self,
        messages: List[Union[Dict[str, str], SystemMessage, HumanMessage, AIMessage]]
    ) -> Any:
        """
        Generate chat completion with default settings.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Response object with content attribute
        """
        try:
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

            response = self.client.chat.completions.create(
                model=Config.CHAT_MODEL,
                messages=formatted_messages
            )
            
            # Return a simple object with content attribute for compatibility
            class CompletionResponse:
                def __init__(self, content):
                    self.content = content
            
            return CompletionResponse(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in get_completion: {e}")
            raise