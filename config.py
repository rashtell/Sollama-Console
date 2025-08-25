"""Configuration constants and settings for Sollama"""

DEFAULT_MODEL = "llama3.2"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_SPEECH_RATE = 175
DEFAULT_VOLUME = 1.0
DEFAULT_MAX_MEMORY = 50
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant with text-to-speech capabilities. You provide clear, concise, and engaging responses. When speaking, you use natural conversational language that sounds good when read aloud. You remember previous parts of our conversation and can reference them when relevant."""

SENTENCE_ENDINGS = r'[.!?]+[\s\n]*'
TTS_QUEUE_TIMEOUT = 0.1
TTS_THREAD_JOIN_TIMEOUT = 1.0

# Installation URLs
OLLAMA_WINDOWS_URL = "https://ollama.ai/download/windows"
OLLAMA_MAC_URL = "https://ollama.ai/download/mac" 
OLLAMA_INSTALL_SCRIPT = "https://ollama.ai/install.sh"
