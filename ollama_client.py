"""Ollama API client and model management"""

import json
import re
import requests
from typing import List, Dict, Tuple, Iterator
from config import DEFAULT_OLLAMA_URL, SENTENCE_ENDINGS


class OllamaClient:
    """Handles communication with Ollama API"""
    
    def __init__(self, model: str, ollama_url: str = DEFAULT_OLLAMA_URL):
        self.model = model
        self.ollama_url = ollama_url
        self.use_streaming = True
    
    def test_connection(self) -> dict:
        """Test connection to ollama server"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to ollama server: {e}")
    
    def get_models(self) -> List[dict]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json().get('models', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error getting models: {e}")
    
    def format_messages_for_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages for Ollama's prompt format"""
        formatted_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                formatted_parts.append(f"System: {content}")
            elif role == "user":
                formatted_parts.append(f"Human: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")
        
        formatted_parts.append("Assistant:")
        return "\n\n".join(formatted_parts)
    
    def generate_response(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Generate response from Ollama with optional streaming"""
        formatted_prompt = self.format_messages_for_ollama(messages)
        
        request_data = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": self.use_streaming
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=120,
                stream=self.use_streaming
            )
            response.raise_for_status()
            
            if self.use_streaming:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'response' in chunk:
                                yield chunk['response']
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                result = response.json()
                yield result.get('response', '')
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def extract_sentences(self, text_buffer: str) -> Tuple[List[str], str]:
        """Extract complete sentences from text buffer"""
        sentences = []
        sentence_endings = re.finditer(SENTENCE_ENDINGS, text_buffer)
        
        last_end = 0
        for match in sentence_endings:
            sentence = text_buffer[last_end:match.end()].strip()
            if sentence:
                sentences.append(sentence)
            last_end = match.end()
        
        remaining = text_buffer[last_end:].strip()
        return sentences, remaining

