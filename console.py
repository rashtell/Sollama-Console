import argparse
import sys

from config import *
from sollama_app import SollamaApp


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Sollama with Memory")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                       help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--url", "-u", default=DEFAULT_OLLAMA_URL,
                       help=f"Ollama server URL (default: {DEFAULT_OLLAMA_URL})")
    parser.add_argument("--rate", "-r", type=int, default=DEFAULT_SPEECH_RATE,
                       help=f"Speech rate (default: {DEFAULT_SPEECH_RATE})")
    parser.add_argument("--volume", "-v", type=float, default=DEFAULT_VOLUME,
                       help=f"Speech volume 0.0-1.0 (default: {DEFAULT_VOLUME})")
    parser.add_argument("--mute", action="store_true",
                       help="Start with audio muted")
    parser.add_argument("--save", "-s", action="store_true",
                       help="Save conversation to file")
    parser.add_argument("--system-prompt", "-sp", type=str,
                       help="Custom system prompt for the assistant")
    parser.add_argument("--max-memory", "-mm", type=int, default=DEFAULT_MAX_MEMORY,
                       help=f"Maximum conversation exchanges to remember (default: {DEFAULT_MAX_MEMORY})")
    parser.add_argument("--load-memory", "-lm", type=str,
                       help="Load conversation memory from file")
    
    args = parser.parse_args()
    
    # Validate volume range
    if not (0.0 <= args.volume <= 1.0):
        print("❌ Error: Volume must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Create and run the application
    app = SollamaApp(
        model=args.model,
        ollama_url=args.url,
        speech_rate=args.rate,
        volume=args.volume,
        save_responses=args.save,
        system_prompt=args.system_prompt,
        max_memory=args.max_memory,
        mute_on_start=args.mute
    )
    
    # Load memory if specified
    if args.load_memory:
        app.memory.load_memory(args.load_memory)
    
    app.run()


if __name__ == "__main__":
    main()
