import queue
import threading
from typing import List, Optional

# Try to import TTS libraries
TTS_ENGINE = None
try:
    import pyttsx3  # type: ignore
    TTS_ENGINE = "pyttsx3"
except ImportError:
    try:
        import win32com.client
        TTS_ENGINE = "sapi"
    except ImportError:
        print("No TTS library found. Install with: pip install pyttsx3")
        print("Or on Windows: pip install pywin32")


class TTSManager:
    """Manages text-to-speech functionality with threading support"""
    
    def __init__(self, speech_rate: int = 175, volume: float = 1.0):
        self.speech_rate = speech_rate
        self.volume = volume
        self.current_voice_id: Optional[str] = None
        self.tts_available = (TTS_ENGINE is not None)
        self.muted = False
        self.volume_before_mute = volume
        
        # Threading components
        self.tts_queue = queue.Queue()
        self.tts_thread: Optional[threading.Thread] = None
        self.tts_stop_event = threading.Event()
        
        self._test_tts_initialization()
    
    def _test_tts_initialization(self):
        """Test TTS availability and display voice information"""
        if TTS_ENGINE == "pyttsx3":
            try:
                test_engine = pyttsx3.init() # type: ignore
                voices = test_engine.getProperty('voices')
                print("Available TTS voices:")
                for i, voice in enumerate(voices):  # type: ignore
                    print(f"  {i}: {voice.name}")
                test_engine.stop()
                del test_engine
                print("✅ TTS (pyttsx3) is available")
            except Exception as e:
                print(f"TTS initialization test failed: {e}")
                self.tts_available = False
                
        elif TTS_ENGINE == "sapi":
            try:
                test_engine = win32com.client.Dispatch("SAPI.SpVoice") # type: ignore
                print("✅ TTS (SAPI) is available")
            except Exception as e:
                print(f"SAPI TTS test failed: {e}")
                self.tts_available = False
    
    def speak_text(self, text: str):
        """Speak text using TTS engine"""
        if not self.tts_available or not text.strip() or self.muted:
            if self.muted:
                print("🔇 Audio is muted")
            return
            
        print("🔊 Speaking response...")
        self._speak_with_engine(text.strip())
        print("✅ Finished speaking")
    
    def speak_text_immediate(self, text: str):
        """Add text to TTS queue for immediate speaking"""
        if self.tts_available and text.strip() and not self.muted:
            self.tts_queue.put(text.strip())
    
    def _speak_with_engine(self, text: str):
        """Internal method to speak using the available TTS engine"""
        if TTS_ENGINE == "pyttsx3":
            tts_engine = None
            try:
                tts_engine = pyttsx3.init() # type: ignore
                tts_engine.setProperty('rate', self.speech_rate)
                tts_engine.setProperty('volume', self.volume)
                
                if self.current_voice_id:
                    try:
                        tts_engine.setProperty('voice', self.current_voice_id) # type: ignore
                    except:
                        pass
                
                tts_engine.say(text)
                tts_engine.runAndWait()
                
            except Exception as e:
                pass  # Silently fail to avoid interrupting flow
            finally:
                if tts_engine:
                    try:
                        tts_engine.stop()
                        del tts_engine
                    except:
                        pass
                        
        elif TTS_ENGINE == "sapi":
            try:
                sapi_engine = win32com.client.Dispatch("SAPI.SpVoice") # type: ignore
                sapi_engine.Speak(text)
            except Exception as e:
                pass  # Silently fail
    
    def start_tts_thread(self):
        """Start the TTS worker thread for streaming"""
        if self.tts_thread is None or not self.tts_thread.is_alive():
            self.tts_stop_event.clear()
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
    
    def stop_tts_thread(self):
        """Stop the TTS worker thread and clear queue"""
        self.tts_stop_event.set()
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break
        if self.tts_thread and self.tts_thread.is_alive():
            self.tts_thread.join(timeout=1.0)
    
    def _tts_worker(self):
        """Worker thread that processes TTS queue"""
        while not self.tts_stop_event.is_set():
            try:
                text = self.tts_queue.get(timeout=0.1)
                if text and text.strip():
                    self._speak_with_engine(text)
                self.tts_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS worker error: {e}")
    
    def get_voices(self) -> List[dict]:
        """Get available TTS voices - must be called from main thread or with COM initialized"""
        voices = []
        if TTS_ENGINE == "pyttsx3":
            try:
                # Initialize COM for this thread if on Windows
                import sys
                if sys.platform == 'win32':
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                    except:
                        pass
                
                temp_engine = pyttsx3.init() # type: ignore
                engine_voices = temp_engine.getProperty('voices')
                for i, voice in enumerate(engine_voices): # type: ignore
                    voices.append({
                        'index': i,
                        'name': voice.name,
                        'id': voice.id,
                        'current': voice.id == self.current_voice_id
                    })
                temp_engine.stop()
                del temp_engine
                
                # Uninitialize COM
                if sys.platform == 'win32':
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except:
                        pass
                        
            except Exception as e:
                print(f"Error getting voices: {e}")
        return voices
    
    def set_voice(self, voice_index: int) -> bool:
        """Set TTS voice by index"""
        if TTS_ENGINE == "pyttsx3":
            try:
                # Initialize COM for this thread if on Windows
                import sys
                if sys.platform == 'win32':
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                    except:
                        pass
                
                temp_engine = pyttsx3.init() # type: ignore
                voices = temp_engine.getProperty('voices')
                if 0 <= voice_index < len(voices): # type: ignore
                    self.current_voice_id = voices[voice_index].id # type: ignore
                    temp_engine.stop()
                    del temp_engine
                    
                    # Uninitialize COM
                    if sys.platform == 'win32':
                        try:
                            import pythoncom
                            pythoncom.CoUninitialize()
                        except:
                            pass
                    return True
                temp_engine.stop()
                del temp_engine
                
                # Uninitialize COM
                if sys.platform == 'win32':
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except:
                        pass
                        
            except Exception as e:
                print(f"Error setting voice: {e}")
        return False
    
    def adjust_rate(self, increase: bool):
        """Adjust speech rate"""
        if increase:
            self.speech_rate = min(300, self.speech_rate + 25)
        else:
            self.speech_rate = max(50, self.speech_rate - 25)
    
    def adjust_volume(self, increase: bool):
        """Adjust volume by 0.1"""
        if increase:
            self.volume = min(1.0, self.volume + 0.1)
        else:
            self.volume = max(0.0, self.volume - 0.1)
    
    def set_volume(self, volume: float) -> bool:
        """Set specific volume level"""
        if 0.0 <= volume <= 1.0:
            self.volume = volume
            if self.muted:
                self.muted = False
            return True
        return False
    
    def toggle_mute(self):
        """Toggle mute state"""
        if not self.muted:
            self.volume_before_mute = self.volume
            self.volume = 0.0
            self.muted = True
        else:
            self.volume = self.volume_before_mute
            self.muted = False
    
    def test_tts(self):
        """Test TTS with sample text"""
        test_text = "This is a test of the text to speech system. Testing one, two, three."
        self.speak_text(test_text)
