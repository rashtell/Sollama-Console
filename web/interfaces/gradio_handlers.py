import tempfile
from datetime import datetime
from typing import Generator, List, Optional, Tuple

import gradio as gr

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
        pass


class GradioHandlers:
    """Handles all Gradio event callbacks"""
    
    def __init__(self, app):
        self.app = app
    
    def _text_to_audio_file(self, text: str) -> Optional[str]:
        """Convert text to audio file for web playback"""
        if not text.strip() or TTS_ENGINE != "pyttsx3" or self.app.tts.muted:
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
            engine.setProperty('rate', self.app.tts.speech_rate)
            engine.setProperty('volume', self.app.tts.volume)
            
            if self.app.tts.current_voice_id:
                try:
                    engine.setProperty('voice', self.app.tts.current_voice_id)
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
        
        if self.app.is_processing:
            yield history + [[message, "Please wait for the current response to complete..."]], None
            return
        
        self.app.is_processing = True
        
        try:
            # Add user message to history
            history = history + [[message, ""]]
            
            # Get full context with message
            messages = self.app.memory.get_full_context()
            messages.append({"role": "user", "content": message})
            
            # Generate response with streaming
            response = ""
            
            for chunk in self.app.client.generate_response(messages):
                response += chunk
                history[-1][1] = response
                yield history, None
            
            # Add to memory
            self.app.memory.add_exchange(message, response)
            self.app.last_response = response
            
            # Generate audio if speak while streaming is enabled
            audio_file = None
            if self.app.speak_while_streaming and TTS_ENGINE == "pyttsx3":
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
            self.app.is_processing = False
    
    def speak_last_response(self) -> Tuple[Optional[str], str]:
        """Speak the last assistant response"""
        if not self.app.last_response:
            return None, "No response to speak"
        
        if TTS_ENGINE != "pyttsx3":
            return None, "TTS not available (pyttsx3 required)"
        
        try:
            audio_file = self._text_to_audio_file(self.app.last_response)
            if audio_file:
                return audio_file, f"Generated audio ({len(self.app.last_response)} characters)"
            return None, "Failed to generate audio"
        except Exception as e:
            return None, f"Error speaking: {str(e)}"
    
    def speak_custom_text(self, text: str) -> Tuple[Optional[str], str]:
        """Speak custom text"""
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
    
    def test_tts(self) -> Tuple[Optional[str], str]:
        """Test TTS with sample text"""
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
    
    def change_voice(self, voice_index: int) -> Tuple[gr.Dropdown, str]:
        """Change TTS voice"""
        if TTS_ENGINE != "pyttsx3":
            return gr.Dropdown(), "TTS not available (pyttsx3 required)"
        
        try:
            if self.app.tts.set_voice(voice_index):
                self.app._load_available_voices()
                voices = self.app.tts.get_voices()
                if voices and voice_index < len(voices):
                    return (
                        gr.Dropdown(choices=self.app.get_voice_choices(), value=voice_index),
                        f"Voice changed to: {voices[voice_index]['name']}"
                    )
            return gr.Dropdown(choices=self.app.get_voice_choices()), "Failed to change voice"
        except Exception as e:
            return gr.Dropdown(choices=self.app.get_voice_choices()), f"Error: {str(e)}"
    
    def refresh_voices(self) -> Tuple[gr.Dropdown, str]:
        """Refresh available voices"""
        self.app._load_available_voices()
        current_index = 0
        if self.app.tts.current_voice_id:
            voices = self.app.tts.get_voices()
            for v in voices:
                if v['current']:
                    current_index = v['index']
                    break
        
        return (
            gr.Dropdown(choices=self.app.get_voice_choices(), value=current_index),
            f"Refreshed! Found {len(self.app.available_voices)} voices"
        )
    
    def update_speech_rate(self, rate: int) -> str:
        """Update speech rate"""
        self.app.tts.speech_rate = rate
        return f"Speech rate: {rate}"
    
    def update_volume(self, volume: float) -> str:
        """Update volume"""
        self.app.tts.volume = volume
        if self.app.tts.muted:
            self.app.tts.muted = False
            return f"Volume: {volume:.1f} (unmuted)"
        return f"Volume: {volume:.1f}"
    
    def update_mute(self, muted: bool) -> str:
        """Update mute state"""
        self.app.tts.muted = muted
        return f"TTS {'muted' if muted else 'unmuted'}"
    
    def toggle_speak_while_streaming(self, enabled: bool) -> str:
        """Toggle speak while streaming"""
        self.app.speak_while_streaming = enabled
        return f"Speak while streaming: {'enabled' if enabled else 'disabled'}"
    
    def clear_memory(self) -> Tuple[List, str]:
        """Clear conversation memory"""
        self.app.memory.clear_history()
        self.app.last_response = ""
        return [], "Memory cleared successfully!"
    
    def get_memory_status(self) -> str:
        """Get memory status"""
        return self.app.memory.get_memory_summary()
    
    def update_system_prompt(self, prompt: str) -> str:
        """Update system prompt"""
        if prompt.strip():
            self.app.memory.set_system_prompt(prompt)
            return f"System prompt updated: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
        return "Please enter a system prompt"
    
    def change_model(self, model_name: str) -> Tuple[str, str]:
        """Change active model"""
        if model_name.strip():
            self.app.client.model = model_name
            return f"Current Model: {model_name}", f"Model changed to: {model_name}"
        return f"Current Model: {self.app.client.model}", "Please select a model"
    
    def refresh_models(self) -> Tuple[gr.Dropdown, str, str]:
        """Refresh available models"""
        self.app._load_available_models()
        return (
            gr.Dropdown(choices=self.app.available_models, value=self.app.client.model),
            f"Current Model: {self.app.client.model}",
            f"Refreshed! Found {len(self.app.available_models)} models"
        )
    
    def save_memory_file(self) -> str:
        """Save memory to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_memory_{timestamp}.json"
        if self.app.memory.save_memory(filename):
            return f"Memory saved to: {filename}"
        return "Failed to save memory"
    
    def load_memory_file(self, file) -> Tuple[List[List], str]:
        """Load memory from file"""
        if file is None:
            return [], "No file selected"
        
        try:
            if self.app.memory.load_memory(file.name):
                history = []
                for i in range(0, len(self.app.memory.conversation_history), 2):
                    if i + 1 < len(self.app.memory.conversation_history):
                        user_msg = self.app.memory.conversation_history[i]['content']
                        assistant_msg = self.app.memory.conversation_history[i + 1]['content']
                        history.append([user_msg, assistant_msg])
                
                return history, f"Memory loaded successfully! Restored {len(history)} exchanges."
            return [], "Failed to load memory"
        except Exception as e:
            return [], f"Error loading memory: {str(e)}"
    
    def toggle_streaming(self, current_state: bool) -> Tuple[bool, str]:
        """Toggle streaming mode"""
        new_state = not current_state
        self.app.client.use_streaming = new_state
        return new_state, f"Streaming mode {'enabled' if new_state else 'disabled'}"