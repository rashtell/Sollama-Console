from datetime import datetime
from typing import Optional

from config import (DEFAULT_MAX_MEMORY, DEFAULT_MODEL, DEFAULT_OLLAMA_URL,
                    DEFAULT_SPEECH_RATE, DEFAULT_VOLUME)
from console.command_handler import CommandHandler
from utils.conversation_logger import ConversationLogger
from utils.memory_manager import ConversationMemory
from utils.ollama_client import OllamaClient
from utils.system_checker import SystemChecker
from utils.tts_manager import TTSManager


class SollamaApp:
    
    def __init__(self, 
                 model: str = DEFAULT_MODEL,
                 ollama_url: str = DEFAULT_OLLAMA_URL,
                 speech_rate: int = DEFAULT_SPEECH_RATE,
                 volume: float = DEFAULT_VOLUME,
                 save_responses: bool = False,
                 system_prompt: Optional[str] = None,
                 max_memory: int = DEFAULT_MAX_MEMORY,
                 mute_on_start: bool = False):
        
        # Initialize core components
        self.memory = ConversationMemory(system_prompt, max_memory)
        self.tts = TTSManager(speech_rate, volume)
        self.client = OllamaClient(model, ollama_url)
        self.logger = ConversationLogger(save_responses)
        self.command_handler = CommandHandler(self.memory, self.tts, self.client)
        
        # Additional settings
        self.speak_while_streaming = True
        
        # Handle mute on start
        if mute_on_start:
            self.tts.volume_before_mute = volume
            self.tts.volume = 0.0
            self.tts.muted = True
    
    def run(self):
        """Main application loop"""
        self._show_startup_info()
        
        if not self._check_system_requirements():
            return
        
        self._show_feature_info()
        
        try:
            while True:
                try:
                    user_input = input("\nYou: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    command_result = self.command_handler.handle_command(user_input)
                    
                    if command_result == 'exit':
                        break
                    elif command_result == 'continue':
                        continue
                    
                    # Process as question
                    self._process_question(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user")
                    break
                except EOFError:
                    break
                    
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        finally:
            self._cleanup_and_exit()
    
    def _show_startup_info(self):
        """Display startup information"""
        print("=" * 70)
        print("      Sollama with Memory - Python Version")
        print("=" * 70)
        print(f"Server: {self.client.ollama_url}")
        print(f"Model: {self.client.model}")
        print(f"Memory: Max {self.memory.max_history} exchanges")
        print(f"System prompt: {len(self.memory.system_prompt)} chars")
        
        # Display audio status
        if not self.tts.tts_available:
            print("⚠️  TTS not available - responses will be text-only")
        else:
            if self.tts.muted:
                print(f"🔇 TTS muted (volume was {self.tts.volume_before_mute:.1f})")
            else:
                print(f"🔊 TTS volume: {self.tts.volume:.1f}")
    
    def _check_system_requirements(self) -> bool:
        """Check system requirements"""
        print("\nChecking Ollama installation...")
        if not SystemChecker.check_ollama_installation():
            print("\nPlease install Ollama first, then run this script again.")
            return False
        
        print("\nTesting connection to ollama server...")
        try:
            server_info = self.client.test_connection()
            print("✅ Connected to ollama server")
            
            models = server_info.get('models', [])
            if not models:
                print("\n⚠️  No models found! You need to pull a model first.")
                print("Run: ollama pull llama3.2")
                return False
                
            print("\nAvailable models:")
            for model in models:
                name = model.get('name', 'Unknown')
                if name == self.client.model:
                    print(f"  • {name} (selected)")
                else:
                    print(f"  • {name}")
            return True
                    
        except ConnectionError as e:
            print(f"❌ {e}")
            print("\nOllama is installed but not running.")
            print("Please run: ollama serve")
            print("Then try this script again.")
            return False
    
    def _show_feature_info(self):
        """Show feature information"""
        print("\n🧠 Memory Features:")
        print("  • Conversation context is preserved across questions")
        print("  • Use 'clear' to start fresh conversation")
        print("  • Use 'memory' to check current memory status")
        print("  • Use 'system <prompt>' to set assistant personality")
        print("  • Use 'save_memory' / 'load_memory' for persistence")
        
        print("\nType 'help' for all commands or start asking questions!")
        print("Type 'test_tts' to test text-to-speech")
        print("Type 'exit' to quit")
        print("=" * 70)
    
    def _process_question(self, user_input: str):
        """Process a user question"""
        self.logger.question_count += 1
        mode_text = "streaming" if self.client.use_streaming else "non-streaming"
        print(f"\n🤔 Asking ollama ({mode_text})...")
        
        try:
            response = self._get_ollama_response(user_input)
            
            if response and response.strip():
                # Add to memory and log
                self.memory.add_exchange(user_input, response)
                self.logger.log_exchange(user_input, response)
                self.command_handler.last_response = response
                
                # Handle TTS if not already spoken during streaming
                if not (self.client.use_streaming and self.speak_while_streaming and self.tts.tts_available):
                    print("\n" + "="*50)
                    if self.tts.tts_available:
                        self.tts.speak_text(response)
                    else:
                        print("⚠️ TTS not available for this response")
            else:
                print("❌ Empty response from ollama")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Make sure ollama server is running: ollama serve")
    
    def _get_ollama_response(self, prompt: str) -> str:
        """Get response from Ollama with context"""
        messages = self.memory.get_full_context()
        messages.append({"role": "user", "content": prompt})
        
        full_response = ""
        text_buffer = ""
        
        print(f"\n🤖 Ollama ({self.client.model}) - {self.memory.get_memory_summary()}:")
        
        # Start TTS thread if streaming with live TTS
        if self.client.use_streaming and self.speak_while_streaming and self.tts.tts_available:
            self.tts.start_tts_thread()
            print("🔊 Speaking as stream arrives...")
        
        # Process response stream
        for chunk in self.client.generate_response(messages):
            full_response += chunk
            text_buffer += chunk
            print(chunk, end='', flush=True)
            
            # Handle live TTS during streaming
            if self.client.use_streaming and self.speak_while_streaming and self.tts.tts_available:
                sentences, text_buffer = self.client.extract_sentences(text_buffer)
                for sentence in sentences:
                    if sentence.strip():
                        self.tts.speak_text_immediate(sentence)
        
        print()  # New line after streaming
        
        # Finish up streaming TTS
        if self.client.use_streaming and self.speak_while_streaming and self.tts.tts_available:
            if text_buffer.strip():
                self.tts.speak_text_immediate(text_buffer)
            self.tts.tts_queue.join()
            self.tts.stop_tts_thread()
            print("✅ Streaming and speaking complete!")
        
        return full_response.strip()
    
    def _cleanup_and_exit(self):
        """Clean up and exit gracefully"""
        self.tts.stop_tts_thread()
        print("\n🎉 Session ended. Thank you!")
        
        if self.logger.conversation_file:
            print(f"💾 Conversation saved to: {self.logger.conversation_file}")
        
        # Offer to save memory
        if len(self.memory.conversation_history) > 0:
            try:
                save_choice = input("Save conversation memory? (y/N): ").lower().strip()
                if save_choice in ['y', 'yes']:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    memory_file = f"ollama_memory_{timestamp}.json"
                    self.memory.save_memory(memory_file)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
