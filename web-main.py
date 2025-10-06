import argparse
import sys
import tempfile
from datetime import datetime
from typing import Generator, List, Optional, Tuple

import gradio as gr

from config import (DEFAULT_MAX_MEMORY, DEFAULT_MODEL, DEFAULT_OLLAMA_URL,
                    DEFAULT_SPEECH_RATE, DEFAULT_VOLUME)
from utils.memory_manager import ConversationMemory
from utils.ollama_client import OllamaClient
from utils.system_checker import SystemChecker
from utils.tts_manager import TTSManager

# Try to import TTS libraries
TTS_ENGINE = None
try:
    import pyttsx3
    TTS_ENGINE = "pyttsx3"
except ImportError:
    try:
        import win32com.client
        TTS_ENGINE = "sapi"
    except ImportError:
        print("No TTS library found. Install with: pip install pyttsx3")


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
    
    def _text_to_audio_file(self, text: str) -> Optional[str]:
        """Convert text to audio file for web playback"""
        if not text.strip() or TTS_ENGINE != "pyttsx3" or self.tts.muted:
            return None
        
        try:
            # Initialize COM for Windows
            import sys
            if sys.platform == 'win32':
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except:
                    pass
            
            # Create temporary audio file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.close()
            
            # Generate audio
            engine = pyttsx3.init() # type: ignore
            engine.setProperty('rate', self.tts.speech_rate)
            engine.setProperty('volume', self.tts.volume)
            
            if self.tts.current_voice_id:
                try:
                    engine.setProperty('voice', self.tts.current_voice_id)
                except:
                    pass
            
            engine.save_to_file(text, temp_file.name)
            engine.runAndWait()
            engine.stop()
            del engine
            
            # Cleanup COM
            if sys.platform == 'win32':
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except:
                    pass
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
        
    def chat_stream(self, message: str, history: List[List]) -> Generator:
        """Process chat message with streaming and return updated history"""
        if not message.strip():
            yield history, None
            return
        
        if self.is_processing:
            yield history + [[message, "Please wait for the current response to complete..."]], None
            return
        
        self.is_processing = True
        
        try:
            # Add user message to history
            history = history + [[message, ""]]
            
            # Get full context with message
            messages = self.memory.get_full_context()
            messages.append({"role": "user", "content": message})
            
            # Generate response with streaming
            response = ""
            
            for chunk in self.client.generate_response(messages):
                response += chunk
                # Update the history with accumulated response
                history[-1][1] = response
                yield history, None
            
            # Add to memory
            self.memory.add_exchange(message, response)
            
            # Store last response for speak feature
            self.last_response = response
            
            # Generate audio if speak while streaming is enabled
            audio_file = None
            if self.speak_while_streaming and TTS_ENGINE == "pyttsx3":
                audio_file = self._text_to_audio_file(response)
            
            yield history, audio_file
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if history and len(history) > 0:
                history[-1][1] = error_msg
            else:
                history = history + [[message, error_msg]]
            yield history, None
        
        finally:
            self.is_processing = False
    
    def speak_last_response(self) -> tuple[Optional[str], str]:
        """Speak the last assistant response - returns audio file for web"""
        if not self.last_response:
            return None, "No response to speak"
        
        if TTS_ENGINE != "pyttsx3":
            return None, "TTS not available (pyttsx3 required)"
        
        try:
            audio_file = self._text_to_audio_file(self.last_response)
            if audio_file:
                return audio_file, f"Generated audio ({len(self.last_response)} characters)"
            return None, "Failed to generate audio"
        except Exception as e:
            return None, f"Error speaking: {str(e)}"
    
    def speak_custom_text(self, text: str) -> tuple[Optional[str], str]:
        """Speak custom text - returns audio file for web"""
        if not text.strip():
            return None, "Please enter text to speak"
        
        if TTS_ENGINE != "pyttsx3":
            return None, "TTS not available (pyttsx3 required)"
        
        try:
            audio_file = self._text_to_audio_file(text)
            if audio_file:
                return audio_file, f"Generated audio ({len(text)} characters)"
            return None, "Failed to generate audio"
        except Exception as e:
            return None, f"Error speaking: {str(e)}"
    
    def test_tts(self) -> tuple[Optional[str], str]:
        """Test TTS with sample text - returns audio file for web"""
        if TTS_ENGINE != "pyttsx3":
            return None, "TTS not available (pyttsx3 required)"
        
        test_text = "This is a test of the text to speech system. Testing one, two, three."
        try:
            audio_file = self._text_to_audio_file(test_text)
            if audio_file:
                return audio_file, "Playing TTS test..."
            return None, "Failed to generate test audio"
        except Exception as e:
            return None, f"Error testing TTS: {str(e)}"
    
    def change_voice(self, voice_index: int) -> tuple[gr.Dropdown, str]:
        """Change TTS voice and update dropdown"""
        if TTS_ENGINE != "pyttsx3":
            return gr.Dropdown(), "TTS not available (pyttsx3 required)"
        
        try:
            if self.tts.set_voice(voice_index):
                # Reload voices to update current marker
                self._load_available_voices()
                voices = self.tts.get_voices()
                if voices and voice_index < len(voices):
                    return (
                        gr.Dropdown(choices=self.get_voice_choices(), value=voice_index),
                        f"Voice changed to: {voices[voice_index]['name']}"
                    )
                return (
                    gr.Dropdown(choices=self.get_voice_choices(), value=voice_index),
                    f"Voice changed to index: {voice_index}"
                )
            return gr.Dropdown(choices=self.get_voice_choices()), "Failed to change voice or invalid voice index"
        except Exception as e:
            return gr.Dropdown(choices=self.get_voice_choices()), f"Error changing voice: {str(e)}"
    
    def refresh_voices(self) -> tuple[gr.Dropdown, str]:
        """Refresh the list of available voices"""
        self._load_available_voices()
        current_index = 0
        if self.tts.current_voice_id:
            voices = self.tts.get_voices()
            for v in voices:
                if v['current']:
                    current_index = v['index']
                    break
        
        return (
            gr.Dropdown(choices=self.get_voice_choices(), value=current_index),
            f"Refreshed! Found {len(self.available_voices)} voices"
        )
    
    def update_speech_rate(self, rate: int) -> str:
        """Update speech rate automatically"""
        self.tts.speech_rate = rate
        return f"Speech rate: {rate}"
    
    def update_volume(self, volume: float) -> str:
        """Update volume automatically"""
        self.tts.volume = volume
        if self.tts.muted:
            self.tts.muted = False
            return f"Volume: {volume:.1f} (unmuted)"
        return f"Volume: {volume:.1f}"
    
    def update_mute(self, muted: bool) -> str:
        """Update mute state automatically"""
        self.tts.muted = muted
        return f"TTS {'muted' if muted else 'unmuted'}"
    
    def toggle_speak_while_streaming(self, enabled: bool) -> str:
        """Toggle speak while streaming"""
        self.speak_while_streaming = enabled
        return f"Speak while streaming: {'enabled' if enabled else 'disabled'}"
    
    def clear_memory(self) -> tuple[List, str]:
        """Clear conversation memory"""
        self.memory.clear_history()
        self.last_response = ""
        return [], "Memory cleared successfully!"
    
    def get_memory_status(self) -> str:
        """Get current memory status"""
        return self.memory.get_memory_summary()
    
    def update_system_prompt(self, prompt: str) -> str:
        """Update system prompt"""
        if prompt.strip():
            self.memory.set_system_prompt(prompt)
            return f"System prompt updated: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
        return "Please enter a system prompt"
    
    def change_model(self, model_name: str) -> tuple[str, str]:
        """Change the active model and return status with current model display"""
        if model_name.strip():
            self.client.model = model_name
            current_model_display = f"Current Model: {model_name}"
            status = f"Model changed to: {model_name}"
            return current_model_display, status
        return f"Current Model: {self.client.model}", "Please select a model"
    
    def refresh_models(self) -> tuple[gr.Dropdown, str, str]:
        """Refresh the list of available models"""
        self._load_available_models()
        current_model_display = f"Current Model: {self.client.model}"
        return (
            gr.Dropdown(choices=self.available_models, value=self.client.model),
            current_model_display,
            f"Refreshed! Found {len(self.available_models)} models"
        )
    
    def get_current_model_display(self) -> str:
        """Get the current model display text"""
        return f"Current Model: {self.client.model}"
    
    def save_memory_file(self) -> str:
        """Save memory to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_memory_{timestamp}.json"
        if self.memory.save_memory(filename):
            return f"Memory saved to: {filename}"
        return "Failed to save memory"
    
    def load_memory_file(self, file) -> tuple[List[List], str]:
        """Load memory from uploaded file"""
        if file is None:
            return [], "No file selected"
        
        try:
            if self.memory.load_memory(file.name):
                # Rebuild chat history from loaded memory in tuple format
                history = []
                for i in range(0, len(self.memory.conversation_history), 2):
                    if i + 1 < len(self.memory.conversation_history):
                        user_msg = self.memory.conversation_history[i]['content']
                        assistant_msg = self.memory.conversation_history[i + 1]['content']
                        history.append([user_msg, assistant_msg])
                
                exchanges = len(history)
                return history, f"Memory loaded successfully! Restored {exchanges} exchanges."
            return [], "Failed to load memory"
        except Exception as e:
            return [], f"Error loading memory: {str(e)}"
    
    def toggle_streaming(self, current_state: bool) -> tuple[bool, str]:
        """Toggle streaming mode"""
        new_state = not current_state
        self.client.use_streaming = new_state
        mode = "enabled" if new_state else "disabled"
        return new_state, f"Streaming mode {mode}"


def create_interface(app: SollamaGradioInterface):
    """Create and configure the Gradio interface"""
    
    # Check system requirements
    if not SystemChecker.check_ollama_installation():
        print("Warning: Ollama not detected. Some features may not work.")
    
    # Get current voice index for dropdown default
    current_voice_index = 0
    if app.tts.current_voice_id:
        voices = app.tts.get_voices()
        for v in voices:
            if v['current']:
                current_voice_index = v['index']
                break
    
    with gr.Blocks(title="Sollama - AI Chat with Memory", theme="soft") as interface:
        
        gr.Markdown("# Sollama - AI Chat with Memory")
        gr.Markdown("Chat with Ollama models with conversation memory and text-to-speech capabilities")
        
        with gr.Row():
            with gr.Column(scale=3):
                # Main chat interface
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    show_copy_button=True
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your message here...",
                        lines=2,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", size="sm")
                    memory_status_btn = gr.Button("Memory Status", size="sm")
                    speak_last_btn = gr.Button("Speak Last Response", size="sm", variant="secondary")
                
                # Audio player for TTS output
                audio_output = gr.Audio(
                    label="TTS Audio",
                    autoplay=True,
                    visible=True
                )
                
                status_output = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2
                )
            
            with gr.Column(scale=1):
                # Settings panel
                gr.Markdown("### Settings")
                
                with gr.Accordion("Model Settings", open=True):
                    # Display current model prominently
                    current_model_display = gr.Textbox(
                        label="Active Model",
                        value=app.get_current_model_display(),
                        interactive=False,
                        show_copy_button=True
                    )
                    
                    model_dropdown = gr.Dropdown(
                        label="Select Model",
                        choices=app.get_model_choices(),
                        value=app.client.model,
                        interactive=True
                    )
                    
                    with gr.Row():
                        refresh_models_btn = gr.Button("Refresh Models", size="sm", scale=1)
                    
                    streaming_checkbox = gr.Checkbox(
                        label="Enable Streaming",
                        value=True
                    )
                    toggle_streaming_btn = gr.Button("Toggle Streaming", size="sm")
                
                with gr.Accordion("System Prompt", open=False):
                    system_prompt = gr.Textbox(
                        label="System Prompt",
                        placeholder="You are a helpful assistant...",
                        lines=4
                    )
                    update_prompt_btn = gr.Button("Update Prompt", size="sm")
                
                with gr.Accordion("TTS Settings", open=False):
                    speak_streaming_checkbox = gr.Checkbox(
                        label="Speak While Streaming",
                        value=app.speak_while_streaming,
                        info="Automatically speak responses as they complete"
                    )
                    
                    tts_rate = gr.Slider(
                        label="Speech Rate",
                        minimum=50,
                        maximum=300,
                        value=app.tts.speech_rate,
                        step=25
                    )
                    tts_volume = gr.Slider(
                        label="Volume",
                        minimum=0.0,
                        maximum=1.0,
                        value=app.tts.volume,
                        step=0.1
                    )
                    tts_mute = gr.Checkbox(
                        label="Mute TTS",
                        value=app.tts.muted
                    )
                    
                    gr.Markdown("#### Voice Selection")
                    voice_dropdown = gr.Dropdown(
                        label="Select Voice",
                        choices=app.get_voice_choices(),
                        value=current_voice_index,
                        interactive=True
                    )
                    refresh_voices_btn = gr.Button("Refresh Voices", size="sm")
                    
                    gr.Markdown("#### TTS Testing")
                    test_tts_btn = gr.Button("Test TTS", size="sm")
                    custom_text_input = gr.Textbox(
                        label="Custom Text to Speak",
                        placeholder="Enter text to speak...",
                        lines=3
                    )
                    speak_custom_btn = gr.Button("Speak Custom Text", size="sm")
                
                with gr.Accordion("Memory Management", open=False):
                    save_memory_btn = gr.Button("Save Memory", size="sm")
                    load_memory_file_input = gr.File(
                        label="Load Memory File",
                        file_types=[".json"]
                    )
                    load_memory_btn = gr.Button("Load Memory", size="sm")
                
                model_status = gr.Textbox(
                    label="Model Status",
                    interactive=False,
                    lines=6
                )
        
        # Event handlers
        
        # Chat functionality with streaming
        msg.submit(
            app.chat_stream,
            inputs=[msg, chatbot],
            outputs=[chatbot, audio_output]
        ).then(
            lambda: "",
            outputs=msg
        )
        
        send_btn.click(
            app.chat_stream,
            inputs=[msg, chatbot],
            outputs=[chatbot, audio_output]
        ).then(
            lambda: "",
            outputs=msg
        )
        
        # Memory management
        clear_btn.click(
            app.clear_memory,
            outputs=[chatbot, status_output]
        )
        
        memory_status_btn.click(
            app.get_memory_status,
            outputs=status_output
        )
        
        save_memory_btn.click(
            app.save_memory_file,
            outputs=model_status
        )
        
        load_memory_btn.click(
            app.load_memory_file,
            inputs=load_memory_file_input,
            outputs=[chatbot, model_status]
        )
        
        # TTS functionality
        speak_last_btn.click(
            app.speak_last_response,
            outputs=[audio_output, status_output]
        )
        
        test_tts_btn.click(
            app.test_tts,
            outputs=[audio_output, model_status]
        )
        
        speak_custom_btn.click(
            app.speak_custom_text,
            inputs=custom_text_input,
            outputs=[audio_output, model_status]
        )
        
        voice_dropdown.change(
            app.change_voice,
            inputs=voice_dropdown,
            outputs=[voice_dropdown, model_status]
        )
        
        refresh_voices_btn.click(
            app.refresh_voices,
            outputs=[voice_dropdown, model_status]
        )
        
        # TTS settings - auto-update
        speak_streaming_checkbox.change(
            app.toggle_speak_while_streaming,
            inputs=speak_streaming_checkbox,
            outputs=model_status
        )
        
        tts_rate.change(
            app.update_speech_rate,
            inputs=tts_rate,
            outputs=model_status
        )
        
        tts_volume.change(
            app.update_volume,
            inputs=tts_volume,
            outputs=model_status
        )
        
        tts_mute.change(
            app.update_mute,
            inputs=tts_mute,
            outputs=model_status
        )
        
        # Model settings
        model_dropdown.change(
            app.change_model,
            inputs=model_dropdown,
            outputs=[current_model_display, model_status]
        )
        
        refresh_models_btn.click(
            app.refresh_models,
            outputs=[model_dropdown, current_model_display, model_status]
        )
        
        toggle_streaming_btn.click(
            app.toggle_streaming,
            inputs=streaming_checkbox,
            outputs=[streaming_checkbox, model_status]
        )
        
        # System prompt
        update_prompt_btn.click(
            app.update_system_prompt,
            inputs=system_prompt,
            outputs=status_output
        )
        
        gr.Markdown("""
        ### Features
        - **Conversation Memory**: Context is preserved across messages
        - **Model Switching**: Change models on the fly
        - **System Prompts**: Customize assistant behavior
        - **Memory Persistence**: Save and load conversation history
        - **TTS Support**: Text-to-speech with audio playback in browser
        - **Streaming Responses**: See responses as they're generated
        - **Auto-Speak**: Optionally speak responses automatically after streaming
        - **Voice Selection**: Choose from available system voices
        - **Custom TTS**: Speak any custom text
        
        **Note**: TTS generates audio files that play in your browser. Requires pyttsx3 to be installed.
        Enable "Speak While Streaming" to automatically hear responses after they finish generating.
        """)
    
    return interface


def main():
    """Launch the Gradio interface with command line arguments"""
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
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.volume < 0.0 or args.volume > 1.0:
        print("Error: Volume must be between 0.0 and 1.0")
        sys.exit(1)
    
    if args.speech_rate < 50 or args.speech_rate > 300:
        print("Error: Speech rate must be between 50 and 300")
        sys.exit(1)
    
    # Parse authentication
    auth_tuple = None
    if args.auth:
        if ':' not in args.auth:
            print("Error: Auth must be in format 'username:password'")
            sys.exit(1)
        auth_tuple = tuple(args.auth.split(':', 1))
    
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
    
    # Launch configuration
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


"""
USAGE EXAMPLES:

Basic Usage:
    python gradio_interface.py

Custom Server Settings:
    python gradio_interface.py --host 0.0.0.0 --port 8080
    python gradio_interface.py --share
    python gradio_interface.py --auth admin:password123

TTS Configuration:
    python gradio_interface.py --speech-rate 200 --volume 0.8
    python gradio_interface.py --voice 2 --speak-streaming
    python gradio_interface.py --mute

Model Configuration:
    python gradio_interface.py --model llama3.2:1b
    python gradio_interface.py --model mistral --ollama-url http://192.168.1.100:11434

Memory Configuration:
    python gradio_interface.py --max-memory 100
    python gradio_interface.py --system-prompt "You are a coding expert"
    python gradio_interface.py --load-memory conversation_20240101.json

Combined Examples:
    # Public server with custom voice and model
    python gradio_interface.py --share --model llama3.2:1b --voice 1 --speak-streaming
    
    # Secure server with authentication
    python gradio_interface.py --host 0.0.0.0 --port 443 --auth user:pass --ssl-certfile cert.pem --ssl-keyfile key.pem
    
    # Custom configuration for specific use case
    python gradio_interface.py --model codellama --system-prompt "You are a Python expert" --speech-rate 150 --volume 0.5

SSL/TLS Setup:
    # Generate self-signed certificate (for testing)
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    
    # Launch with SSL
    python gradio_interface.py --ssl-certfile cert.pem --ssl-keyfile key.pem --port 443

Reverse Proxy Setup:
    # Behind nginx or apache
    python gradio_interface.py --root-path /sollama --host 127.0.0.1 --port 7860

Environment Variables (alternative to command line):
    export SOLLAMA_HOST=0.0.0.0
    export SOLLAMA_PORT=8080
    export SOLLAMA_MODEL=llama3.2:1b
    python gradio_interface.py
"""