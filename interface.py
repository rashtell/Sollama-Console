# File: gradio_interface.py
"""Gradio web interface for Sollama"""

import gradio as gr
import threading
from typing import List, Dict, Optional
from datetime import datetime

from config import DEFAULT_MODEL, DEFAULT_OLLAMA_URL, DEFAULT_SPEECH_RATE, DEFAULT_VOLUME, DEFAULT_MAX_MEMORY
from memory_manager import ConversationMemory
from tts_manager import TTSManager
from ollama_client import OllamaClient
from system_checker import SystemChecker


class SollamaGradioInterface:
    """Gradio web interface for Sollama"""
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.tts = TTSManager()
        self.client = OllamaClient(DEFAULT_MODEL)
        self.is_processing = False
        self.available_models = []
        self.last_response = ""
        self._load_available_models()
        
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
    
    def get_model_choices(self) -> List[str]:
        """Get list of available models for dropdown"""
        return self.available_models if self.available_models else [DEFAULT_MODEL]
        
    def chat(self, message: str, history: List[Dict]) -> List[Dict]:
        """Process chat message and return updated history"""
        if not message.strip():
            return history
        
        if self.is_processing:
            history.append({
                "role": "assistant",
                "content": "Please wait for the current response to complete..."
            })
            return history
        
        self.is_processing = True
        
        try:
            # Add user message to history
            history.append({"role": "user", "content": message})
            
            # Get full context with message
            messages = self.memory.get_full_context()
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = ""
            for chunk in self.client.generate_response(messages):
                response += chunk
            
            # Add to memory
            self.memory.add_exchange(message, response)
            
            # Store last response for speak feature
            self.last_response = response
            
            # Add assistant response to history
            history.append({"role": "assistant", "content": response})
            
            return history
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            history.append({"role": "assistant", "content": error_msg})
            return history
        
        finally:
            self.is_processing = False
    
    def speak_last_response(self) -> str:
        """Speak the last assistant response"""
        if not self.last_response:
            return "No response to speak"
        
        if not self.tts.tts_available:
            return "TTS not available on this system"
        
        try:
            # Start speaking in a separate thread to avoid blocking UI
            threading.Thread(
                target=self.tts.speak_text,
                args=(self.last_response,),
                daemon=True
            ).start()
            return f"Speaking response ({len(self.last_response)} characters)..."
        except Exception as e:
            return f"Error speaking: {str(e)}"
    
    def speak_custom_text(self, text: str) -> str:
        """Speak custom text"""
        if not text.strip():
            return "Please enter text to speak"
        
        if not self.tts.tts_available:
            return "TTS not available on this system"
        
        try:
            # Start speaking in a separate thread to avoid blocking UI
            threading.Thread(
                target=self.tts.speak_text,
                args=(text,),
                daemon=True
            ).start()
            return f"Speaking text ({len(text)} characters)..."
        except Exception as e:
            return f"Error speaking: {str(e)}"
    
    def test_tts(self) -> str:
        """Test TTS with sample text"""
        if not self.tts.tts_available:
            return "TTS not available on this system"
        
        test_text = "This is a test of the text to speech system. Testing one, two, three."
        try:
            threading.Thread(
                target=self.tts.speak_text,
                args=(test_text,),
                daemon=True
            ).start()
            return "Playing TTS test..."
        except Exception as e:
            return f"Error testing TTS: {str(e)}"
    
    def get_available_voices(self) -> str:
        """Get list of available TTS voices"""
        if not self.tts.tts_available:
            return "TTS not available on this system"
        
        try:
            voices = self.tts.get_voices()
            if not voices:
                return "No voices found"
            
            voice_list = "Available voices:\n\n"
            for voice in voices:
                marker = " (CURRENT)" if voice['current'] else ""
                voice_list += f"{voice['index']}: {voice['name']}{marker}\n"
            return voice_list
        except Exception as e:
            return f"Error getting voices: {str(e)}"
    
    def change_voice(self, voice_index: int) -> str:
        """Change TTS voice"""
        if not self.tts.tts_available:
            return "TTS not available on this system"
        
        try:
            if self.tts.set_voice(voice_index):
                voices = self.tts.get_voices()
                if voices and voice_index < len(voices):
                    return f"Voice changed to: {voices[voice_index]['name']}"
                return f"Voice changed to index: {voice_index}"
            return "Failed to change voice or invalid voice index"
        except Exception as e:
            return f"Error changing voice: {str(e)}"
    
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
    
    def load_memory_file(self, file) -> tuple[List[Dict], str]:
        """Load memory from uploaded file"""
        if file is None:
            return [], "No file selected"
        
        try:
            if self.memory.load_memory(file.name):
                # Rebuild chat history from loaded memory in messages format
                history = []
                for i in range(0, len(self.memory.conversation_history), 2):
                    if i + 1 < len(self.memory.conversation_history):
                        history.append(self.memory.conversation_history[i])
                        history.append(self.memory.conversation_history[i + 1])
                
                exchanges = len(history) // 2
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
    
    def adjust_tts_settings(self, rate: int, volume: float, muted: bool) -> str:
        """Adjust TTS settings"""
        self.tts.speech_rate = rate
        self.tts.volume = volume
        self.tts.muted = muted
        
        status = f"TTS Settings Updated:\n"
        status += f"Rate: {rate}\n"
        status += f"Volume: {volume:.1f}\n"
        status += f"Muted: {'Yes' if muted else 'No'}"
        return status


def create_interface():
    """Create and configure the Gradio interface"""
    
    app = SollamaGradioInterface()
    
    # Check system requirements
    if not SystemChecker.check_ollama_installation():
        print("Warning: Ollama not detected. Some features may not work.")
    
    with gr.Blocks(title="Sollama - AI Chat with Memory", theme=gr.themes.Soft()) as interface:
        
        gr.Markdown("# Sollama - AI Chat with Memory")
        gr.Markdown("Chat with Ollama models with conversation memory and text-to-speech capabilities")
        
        with gr.Row():
            with gr.Column(scale=3):
                # Main chat interface
                chatbot = gr.Chatbot(
                    label="Conversation",
                    type="messages",
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
                    tts_rate = gr.Slider(
                        label="Speech Rate",
                        minimum=50,
                        maximum=300,
                        value=DEFAULT_SPEECH_RATE,
                        step=25
                    )
                    tts_volume = gr.Slider(
                        label="Volume",
                        minimum=0.0,
                        maximum=1.0,
                        value=DEFAULT_VOLUME,
                        step=0.1
                    )
                    tts_mute = gr.Checkbox(
                        label="Mute TTS",
                        value=False
                    )
                    apply_tts_btn = gr.Button("Apply TTS Settings", size="sm")
                    
                    gr.Markdown("#### Voice Selection")
                    list_voices_btn = gr.Button("List Available Voices", size="sm")
                    voice_index_input = gr.Number(
                        label="Voice Index",
                        value=0,
                        precision=0,
                        minimum=0
                    )
                    change_voice_btn = gr.Button("Change Voice", size="sm")
                    
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
        
        # Chat functionality
        def submit_message(message, history):
            new_history = app.chat(message, history)
            return new_history, ""
        
        msg.submit(
            submit_message,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        send_btn.click(
            submit_message,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
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
            outputs=status_output
        )
        
        test_tts_btn.click(
            app.test_tts,
            outputs=model_status
        )
        
        speak_custom_btn.click(
            app.speak_custom_text,
            inputs=custom_text_input,
            outputs=model_status
        )
        
        list_voices_btn.click(
            app.get_available_voices,
            outputs=model_status
        )
        
        change_voice_btn.click(
            app.change_voice,
            inputs=voice_index_input,
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
        
        # TTS settings
        apply_tts_btn.click(
            app.adjust_tts_settings,
            inputs=[tts_rate, tts_volume, tts_mute],
            outputs=model_status
        )
        
        gr.Markdown("""
        ### Features
        - **Conversation Memory**: Context is preserved across messages
        - **Model Switching**: Change models on the fly
        - **System Prompts**: Customize assistant behavior
        - **Memory Persistence**: Save and load conversation history
        - **TTS Support**: Text-to-speech capabilities (desktop only)
        - **Streaming**: Real-time response generation
        - **Voice Selection**: Choose from available system voices
        - **Custom TTS**: Speak any custom text
        """)
    
    return interface


def main():
    """Launch the Gradio interface"""
    interface = create_interface()
    interface.launch(
        share=False,
        server_name="127.0.0.1",
        server_port=None,
        show_error=True
    )


if __name__ == "__main__":
    main()