"""Usage examples and documentation for Gradio interface"""

USAGE_EXAMPLES = """
USAGE EXAMPLES:

Basic Usage:
    python -m interfaces.gradio_app

Custom Server Settings:
    python -m interfaces.gradio_app --host 0.0.0.0 --port 8080
    python -m interfaces.gradio_app --share
    python -m interfaces.gradio_app --auth admin:password123

TTS Configuration:
    python -m interfaces.gradio_app --speech-rate 200 --volume 0.8
    python -m interfaces.gradio_app --voice 2 --speak-streaming
    python -m interfaces.gradio_app --mute

Model Configuration:
    python -m interfaces.gradio_app --model llama3.2:1b
    python -m interfaces.gradio_app --model mistral --ollama-url http://192.168.1.100:11434

Memory Configuration:
    python -m interfaces.gradio_app --max-memory 100
    python -m interfaces.gradio_app --system-prompt "You are a coding expert"
    python -m interfaces.gradio_app --load-memory conversation_20240101.json

Combined Examples:
    # Public server with custom voice and model
    python -m interfaces.gradio_app --share --model llama3.2:1b --voice 1 --speak-streaming
    
    # Secure server with authentication
    python -m interfaces.gradio_app --host 0.0.0.0 --port 443 --auth user:pass --ssl-certfile cert.pem --ssl-keyfile key.pem
    
    # Custom configuration for specific use case
    python -m interfaces.gradio_app --model codellama --system-prompt "You are a Python expert" --speech-rate 150 --volume 0.5

SSL/TLS Setup:
    # Generate self-signed certificate (for testing)
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    
    # Launch with SSL
    python -m interfaces.gradio_app --ssl-certfile cert.pem --ssl-keyfile key.pem --port 443

Reverse Proxy Setup:
    # Behind nginx or apache
    python -m interfaces.gradio_app --root-path /sollama --host 127.0.0.1 --port 7860
"""

if __name__ == "__main__":
    print(USAGE_EXAMPLES)