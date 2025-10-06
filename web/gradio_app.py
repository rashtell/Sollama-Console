from typing import List, Tuple

from config import (DEFAULT_MAX_MEMORY, DEFAULT_MODEL, DEFAULT_OLLAMA_URL,
                    DEFAULT_SPEECH_RATE, DEFAULT_VOLUME)
from utils.memory_manager import ConversationMemory
from utils.ollama_client import OllamaClient
from utils.system_checker import SystemChecker
from utils.tts_manager import TTSManager

from .interfaces.gradio_handlers import GradioHandlers
from .interfaces.gradio_ui import GradioUI


class SollamaGradioInterface:
    """Gradio web interface for Sollama"""
    
    def __init__(self, 
                 model: str = DEFAULT_MODEL,
                 speech_rate: int = DEFAULT_SPEECH_RATE,
                 volume: float = DEFAULT_VOLUME,
                 voice_index: int = 0,
                 muted: bool = False,
                 speak_while_streaming: bool = False):
        
        self.memory = ConversationMemory()
        self.tts = TTSManager(speech_rate, volume)
        self.client = OllamaClient(model)
        self.is_processing = False
        self.available_models = []
        self.available_voices = []
        self.last_response = ""
        self.speak_while_streaming = speak_while_streaming
        self.tts.muted = muted
        
        self._load_available_models()
        self._load_available_voices()
        
        # Set initial voice if specified
        if voice_index > 0:
            self.tts.set_voice(voice_index)
        
        # Initialize handlers
        self.handlers = GradioHandlers(self)
        
    def _load_available_models(self):
        """Load available models on initialization"""
        try:
            models = self.client.get_models()
            self.available_models = [model.get('name', 'Unknown') for model in models]
            if not self.available_models:
                self.available_models = [DEFAULT_MODEL]
        except Exception as e:
            print(f"Error loading models: {e}")
            self.available_models = [DEFAULT_MODEL]
    
    def _load_available_voices(self):
        """Load available TTS voices on initialization"""
        try:
            voices = self.tts.get_voices()
            self.available_voices = [(f"{v['index']}: {v['name']}", v['index']) for v in voices]
            if not self.available_voices:
                self.available_voices = [("No voices available", 0)]
        except Exception as e:
            print(f"Error loading voices: {e}")
            self.available_voices = [("Error loading voices", 0)]
    
    def get_model_choices(self) -> List[str]:
        """Get list of available models for dropdown"""
        return self.available_models if self.available_models else [DEFAULT_MODEL]
    
    def get_voice_choices(self) -> List[Tuple[str, int]]:
        """Get list of available voices for dropdown"""
        return self.available_voices
    
    def get_current_model_display(self) -> str:
        """Get the current model display text"""
        return f"Current Model: {self.client.model}"


def create_interface(app: SollamaGradioInterface):
    """Create and configure the Gradio interface"""
    
    # Check system requirements
    if not SystemChecker.check_ollama_installation():
        print("Warning: Ollama not detected. Some features may not work.")
    
    # Create UI
    ui = GradioUI(app)
    interface = ui.build()
    
    return interface


def main():
    """Launch the Gradio interface with command line arguments"""
    from .cli_args import (parse_arguments, print_launch_info,
                           validate_arguments)
    
    args = parse_arguments()
    validate_arguments(args)
    
    # Create the application
    print("Initializing Sollama...")
    app = SollamaGradioInterface(
        model=args.model,
        speech_rate=args.speech_rate,
        volume=args.volume,
        voice_index=args.voice,
        muted=args.mute,
        speak_while_streaming=args.speak_streaming
    )
    
    # Update Ollama URL if specified
    if args.ollama_url != DEFAULT_OLLAMA_URL:
        app.client.ollama_url = args.ollama_url
    
    # Update memory settings if specified
    if args.max_memory != DEFAULT_MAX_MEMORY:
        app.memory.max_history = args.max_memory
    
    if args.system_prompt:
        app.memory.set_system_prompt(args.system_prompt)
    
    if args.load_memory:
        app.memory.load_memory(args.load_memory)
    
    # Create interface
    interface = create_interface(app)
    
    # Print launch info
    print_launch_info(args)
    
    # Parse authentication
    auth_tuple = None
    if args.auth:
        auth_tuple = tuple(args.auth.split(':', 1))
    
    # Launch interface
    interface.launch(
        share=args.share,
        server_name=args.host if not args.server_name else args.server_name,
        server_port=args.port,
        show_error=True,
        auth=auth_tuple,
        root_path=args.root_path,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile
    )


if __name__ == "__main__":
    main()