"""Command handling and help system"""

from datetime import datetime

from memory_manager import ConversationMemory
from ollama_client import OllamaClient
from tts_manager import TTSManager


class CommandHandler:
    """Handles interactive commands and help system"""
    
    def __init__(self, memory: ConversationMemory, tts: TTSManager, client: OllamaClient):
        self.memory = memory
        self.tts = tts
        self.client = client
        self.last_response = ""
    
    def handle_command(self, input_text: str) -> str:
        """Handle special commands and return action type"""
        input_lower = input_text.lower().strip()
        
        # Exit commands
        if input_lower in ['exit', 'quit', 'bye']:
            return 'exit'
        
        # Memory management
        elif input_lower in ['clear', 'new', 'reset']:
            self.memory.clear_history()
            return 'continue'
        
        elif input_lower == 'memory':
            self._show_memory_status()
            return 'continue'
        
        elif input_lower.startswith('system '):
            self._handle_system_prompt(input_text[7:].strip())
            return 'continue'
        
        elif input_lower.startswith('save_memory '):
            self._handle_save_memory(input_text[12:].strip())
            return 'continue'
        
        elif input_lower.startswith('load_memory '):
            self._handle_load_memory(input_text[12:].strip())
            return 'continue'
        
        # Model management
        elif input_lower == 'models':
            self._show_models()
            return 'continue'
        
        elif input_lower.startswith('model '):
            self._switch_model(input_text[6:].strip())
            return 'continue'
        
        elif input_lower == 'stream':
            self._toggle_streaming()
            return 'continue'
        
        # TTS and audio controls
        elif input_lower == 'repeat':
            self._repeat_response()
            return 'continue'
        
        elif input_lower == 'test_tts':
            self.tts.test_tts()
            return 'continue'
        
        elif input_lower == 'voice':
            self._show_voices()
            return 'continue'
        
        elif input_lower.startswith('voice '):
            self._switch_voice(input_text[6:].strip())
            return 'continue'
        
        elif input_lower in ['faster', 'slower']:
            self._adjust_speech_rate(input_lower == 'faster')
            return 'continue'
        
        elif input_lower in ['louder', 'quieter']:
            self._adjust_volume(input_lower == 'louder')
            return 'continue'
        
        elif input_lower in ['mute', 'unmute']:
            self._toggle_mute()
            return 'continue'
        
        elif input_lower.startswith('volume '):
            self._set_volume(input_text[7:].strip())
            return 'continue'
        
        elif input_lower == 'help':
            self.show_help()
            return 'continue'
        
        return 'process'
    
    def _show_memory_status(self):
        """Display current memory status"""
        exchanges = len(self.memory.conversation_history) // 2
        print(f"\n🧠 Memory Status:")
        print(f"   Exchanges: {exchanges}")
        print(f"   Max history: {self.memory.max_history}")
        print(f"   System prompt: {len(self.memory.system_prompt)} chars")
        if exchanges > 0:
            duration = datetime.now() - self.memory.conversation_start_time
            print(f"   Session time: {duration.total_seconds()/60:.1f} minutes")
    
    def _handle_system_prompt(self, prompt: str):
        """Handle system prompt command"""
        if prompt:
            self.memory.set_system_prompt(prompt)
            print(f"System prompt set to: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        else:
            print(f"Current system prompt: {self.memory.system_prompt}")
    
    def _handle_save_memory(self, filename: str):
        """Handle save memory command"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ollama_memory_{timestamp}.json"
        self.memory.save_memory(filename)
    
    def _handle_load_memory(self, filename: str):
        """Handle load memory command"""
        if filename:
            self.memory.load_memory(filename)
        else:
            print("Please specify a filename: load_memory filename.json")
    
    def _show_models(self):
        """Display available models"""
        try:
            models = self.client.get_models()
            print("\nAvailable models:")
            for model in models:
                name = model.get('name', 'Unknown')
                if name == self.client.model:
                    print(f"  • {name} (current)")
                else:
                    print(f"  • {name}")
        except Exception as e:
            print(f"Error: {e}")
    
    def _switch_model(self, model_name: str):
        """Switch to a different model"""
        print(f"Switching to model: {model_name}")
        self.client.model = model_name
    
    def _toggle_streaming(self):
        """Toggle streaming mode"""
        self.client.use_streaming = not self.client.use_streaming
        mode = "enabled" if self.client.use_streaming else "disabled"
        print(f"Streaming mode {mode}")
    
    def _repeat_response(self):
        """Repeat the last response"""
        if self.last_response:
            print("\nRepeating last response...")
            print(f"🤖 Ollama ({self.client.model}):")
            print(self.last_response)
            print("="*50)
            self.tts.speak_text(self.last_response)
        else:
            print("No previous response to repeat")
    
    def _show_voices(self):
        """Show available TTS voices"""
        voices = self.tts.get_voices()
        if voices:
            print("\nAvailable voices:")
            for voice in voices:
                marker = " (current)" if voice['current'] else ""
                print(f"  {voice['index']}: {voice['name']}{marker}")
        else:
            print("No voices available or TTS not supported")
    
    def _switch_voice(self, voice_str: str):
        """Switch TTS voice"""
        try:
            voice_num = int(voice_str)
            if self.tts.set_voice(voice_num):
                voices = self.tts.get_voices()
                if voices and voice_num < len(voices):
                    print(f"Changed to voice: {voices[voice_num]['name']}")
            else:
                print("Failed to change voice or invalid voice number")
        except ValueError:
            print("Invalid voice number")
    
    def _adjust_speech_rate(self, faster: bool):
        """Adjust speech rate"""
        self.tts.adjust_rate(faster)
        print(f"Speech rate: {self.tts.speech_rate}")
    
    def _adjust_volume(self, louder: bool):
        """Adjust volume"""
        self.tts.adjust_volume(louder)
        print(f"Volume: {self.tts.volume:.1f}")
    
    def _toggle_mute(self):
        """Toggle mute state"""
        was_muted = self.tts.muted
        self.tts.toggle_mute()
        if was_muted:
            print(f"🔊 Audio unmuted - Volume: {self.tts.volume:.1f}")
        else:
            print("🔇 Audio muted")
    
    def _set_volume(self, volume_str: str):
        """Set specific volume level"""
        try:
            volume = float(volume_str)
            if self.tts.set_volume(volume):
                status = "(unmuted)" if self.tts.muted else ""
                print(f"🔊 Volume set to {self.tts.volume:.1f} {status}")
            else:
                print("❌ Volume must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid volume value. Use: volume 0.5")
    
    def show_help(self):
        """Display comprehensive help information"""
        print("\n" + "="*70)
        print("                    SOLLAMA HELP")
        print("="*70)
        
        print("\n🗣️  CONVERSATION COMMANDS:")
        print("  <question>            - Ask ollama a question with memory context")
        print("  exit/quit/bye         - Exit the program")
        print("  repeat                - Repeat last response with TTS")
        
        print("\n🧠  MEMORY MANAGEMENT:")
        print("  memory                - Show current memory status")
        print("  clear/new/reset       - Clear conversation memory (start fresh)")
        print("  system <prompt>       - Set/view system prompt for assistant personality")
        print("  save_memory [file]    - Save conversation memory to JSON file")
        print("  load_memory <file>    - Load conversation memory from JSON file")
        
        print("\n🤖  MODEL MANAGEMENT:")
        print("  models                - List all available Ollama models")
        print("  model <name>          - Switch to different model (e.g., llama3.2:1b)")
        print("  stream                - Toggle streaming/non-streaming mode")
        
        print("\n🔊  AUDIO CONTROLS:")
        print("  test_tts              - Test TTS with sample text")
        print("  mute/unmute           - Instantly mute/unmute all audio")
        print("  volume <0.0-1.0>      - Set exact volume (e.g., volume 0.5)")
        print("  louder/quieter        - Adjust volume by ±0.1")
        print("  faster/slower         - Adjust speech rate by ±25")
        
        print("\n🎭  VOICE CONTROLS:")
        print("  voice                 - List all available TTS voices")
        print("  voice <number>        - Switch to voice by number (e.g., voice 2)")
        
        print("\n💡  COMMAND LINE USAGE:")
        print("  Start with custom settings:")
        print("    python main.py --volume 0.5 --mute")
        print("    python main.py --model llama3.2:1b --rate 200")
        print("    python main.py --system-prompt 'You are a coding expert'")
        print("    python main.py --load-memory session.json")
        
        print("\n📊  MEMORY FEATURES:")
        print("  • Assistant remembers your entire conversation")
        print("  • References previous questions and responses")
        print("  • Maintains context across multiple exchanges")
        print("  • Configurable memory limit (default: 50 exchanges)")
        print("  • Persistent memory save/load functionality")
        
        print("\n🎵  AUDIO FEATURES:")
        print("  • Real-time TTS during streaming responses")
        print("  • Multiple TTS engine support (pyttsx3, SAPI)")
        print("  • Voice selection and customization")
        print("  • Precise volume and rate control")
        print("  • Smart mute system with volume memory")
        print("  • Command line audio configuration")
        
        print("\n" + "="*70)

