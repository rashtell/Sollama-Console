import argparse
import sys

from config import (DEFAULT_MAX_MEMORY, DEFAULT_MODEL, DEFAULT_OLLAMA_URL,
                    DEFAULT_SPEECH_RATE, DEFAULT_VOLUME)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Sollama Gradio Web Interface",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Server settings
    server_group = parser.add_argument_group('Server Settings')
    server_group.add_argument("--host", "-H", default="127.0.0.1",
                             help="Host to bind the server to")
    server_group.add_argument("--port", "-p", type=int, default=None,
                             help="Port to run the server on (auto-select if not specified)")
    server_group.add_argument("--share", action="store_true",
                             help="Create a public shareable link")
    server_group.add_argument("--auth", type=str, metavar="USER:PASS",
                             help="Username and password for authentication (format: user:pass)")
    server_group.add_argument("--server-name", type=str, default=None,
                             help="Server name for custom domain")
    server_group.add_argument("--root-path", type=str, default=None,
                             help="Root path for reverse proxy")
    server_group.add_argument("--ssl-certfile", type=str, default=None,
                             help="Path to SSL certificate file")
    server_group.add_argument("--ssl-keyfile", type=str, default=None,
                             help="Path to SSL key file")
    
    # Model settings
    model_group = parser.add_argument_group('Model Settings')
    model_group.add_argument("--model", "-m", default=DEFAULT_MODEL,
                            help="Ollama model to use")
    model_group.add_argument("--ollama-url", "-u", default=DEFAULT_OLLAMA_URL,
                            help="Ollama server URL")
    
    # TTS settings
    tts_group = parser.add_argument_group('TTS Settings')
    tts_group.add_argument("--speech-rate", "-r", type=int, default=DEFAULT_SPEECH_RATE,
                          help="Speech rate (50-300)")
    tts_group.add_argument("--volume", "-v", type=float, default=DEFAULT_VOLUME,
                          help="Speech volume (0.0-1.0)")
    tts_group.add_argument("--voice", type=int, default=0,
                          help="Voice index to use (0 for default)")
    tts_group.add_argument("--mute", action="store_true",
                          help="Start with TTS muted")
    tts_group.add_argument("--speak-streaming", action="store_true",
                          help="Automatically speak responses after streaming")
    
    # Memory settings
    memory_group = parser.add_argument_group('Memory Settings')
    memory_group.add_argument("--max-memory", "-mm", type=int, default=DEFAULT_MAX_MEMORY,
                             help="Maximum conversation exchanges to remember")
    memory_group.add_argument("--system-prompt", "-sp", type=str,
                             help="Custom system prompt for the assistant")
    memory_group.add_argument("--load-memory", "-lm", type=str,
                             help="Load conversation memory from file")
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command-line arguments"""
    if args.volume < 0.0 or args.volume > 1.0:
        print("Error: Volume must be between 0.0 and 1.0")
        sys.exit(1)
    
    if args.speech_rate < 50 or args.speech_rate > 300:
        print("Error: Speech rate must be between 50 and 300")
        sys.exit(1)
    
    if args.auth and ':' not in args.auth:
        print("Error: Auth must be in format 'username:password'")
        sys.exit(1)


def print_launch_info(args):
    """Print launch configuration information"""
    print("\nLaunching Gradio interface...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port if args.port else 'auto-select'}")
    print(f"  Share: {args.share}")
    print(f"  Model: {args.model}")
    print(f"  Speech Rate: {args.speech_rate}")
    print(f"  Volume: {args.volume}")
    print(f"  Voice Index: {args.voice}")
    print(f"  Muted: {args.mute}")
    print(f"  Speak While Streaming: {args.speak_streaming}")
    print()