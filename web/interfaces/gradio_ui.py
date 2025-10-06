import gradio as gr


class GradioUI:
    """Builds the Gradio interface layout"""
    
    def __init__(self, app):
        self.app = app
        self.handlers = app.handlers
    
    def build(self):
        """Build and return the complete Gradio interface"""
        # Get current voice index
        current_voice_index = self._get_current_voice_index()
        
        with gr.Blocks(title="Sollama - AI Chat with Memory", theme="soft") as interface:
            self._build_header()
            
            with gr.Row():
                # Left column - Chat interface
                with gr.Column(scale=3):
                    chatbot, msg, send_btn, audio_output, status_output = self._build_chat_section()
                
                # Right column - Settings
                with gr.Column(scale=1):
                    components = self._build_settings_section(current_voice_index)
            
            self._build_footer()
            
            # Connect event handlers
            self._connect_events(chatbot, msg, send_btn, audio_output, status_output, components)
        
        return interface
    
    def _get_current_voice_index(self):
        """Get current voice index for dropdown"""
        current_voice_index = 0
        if self.app.tts.current_voice_id:
            voices = self.app.tts.get_voices()
            for v in voices:
                if v['current']:
                    current_voice_index = v['index']
                    break
        return current_voice_index
    
    def _build_header(self):
        """Build header section"""
        gr.Markdown("# Sollama - AI Chat with Memory")
        gr.Markdown("Chat with Ollama models with conversation memory and text-to-speech capabilities")
    
    def _build_chat_section(self):
        """Build chat interface section"""
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
        
        # Store button references for event binding
        self.clear_btn = clear_btn
        self.memory_status_btn = memory_status_btn
        self.speak_last_btn = speak_last_btn
        
        return chatbot, msg, send_btn, audio_output, status_output
    
    def _build_settings_section(self, current_voice_index):
        """Build settings panel"""
        gr.Markdown("### Settings")
        
        components = {}
        
        # Model Settings
        with gr.Accordion("Model Settings", open=True):
            components.update(self._build_model_settings())
        
        # System Prompt
        with gr.Accordion("System Prompt", open=False):
            components.update(self._build_system_prompt())
        
        # TTS Settings
        with gr.Accordion("TTS Settings", open=False):
            components.update(self._build_tts_settings(current_voice_index))
        
        # Memory Management
        with gr.Accordion("Memory Management", open=False):
            components.update(self._build_memory_management())
        
        # Model Status
        components['model_status'] = gr.Textbox(
            label="Model Status",
            interactive=False,
            lines=6
        )
        
        return components
    
    def _build_model_settings(self):
        """Build model settings section"""
        current_model_display = gr.Textbox(
            label="Active Model",
            value=self.app.get_current_model_display(),
            interactive=False,
            show_copy_button=True
        )
        
        model_dropdown = gr.Dropdown(
            label="Select Model",
            choices=self.app.get_model_choices(),
            value=self.app.client.model,
            interactive=True
        )
        
        with gr.Row():
            refresh_models_btn = gr.Button("Refresh Models", size="sm", scale=1)
        
        streaming_checkbox = gr.Checkbox(
            label="Enable Streaming",
            value=True
        )
        toggle_streaming_btn = gr.Button("Toggle Streaming", size="sm")
        
        return {
            'current_model_display': current_model_display,
            'model_dropdown': model_dropdown,
            'refresh_models_btn': refresh_models_btn,
            'streaming_checkbox': streaming_checkbox,
            'toggle_streaming_btn': toggle_streaming_btn
        }
    
    def _build_system_prompt(self):
        """Build system prompt section"""
        system_prompt = gr.Textbox(
            label="System Prompt",
            placeholder="You are a helpful assistant...",
            lines=4
        )
        update_prompt_btn = gr.Button("Update Prompt", size="sm")
        
        return {
            'system_prompt': system_prompt,
            'update_prompt_btn': update_prompt_btn
        }
    
    def _build_tts_settings(self, current_voice_index):
        """Build TTS settings section"""
        speak_streaming_checkbox = gr.Checkbox(
            label="Speak While Streaming",
            value=self.app.speak_while_streaming,
            info="Automatically speak responses as they complete"
        )
        
        tts_rate = gr.Slider(
            label="Speech Rate",
            minimum=50,
            maximum=300,
            value=self.app.tts.speech_rate,
            step=25
        )
        
        tts_volume = gr.Slider(
            label="Volume",
            minimum=0.0,
            maximum=1.0,
            value=self.app.tts.volume,
            step=0.1
        )
        
        tts_mute = gr.Checkbox(
            label="Mute TTS",
            value=self.app.tts.muted
        )
        
        gr.Markdown("#### Voice Selection")
        voice_dropdown = gr.Dropdown(
            label="Select Voice",
            choices=self.app.get_voice_choices(),
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
        
        return {
            'speak_streaming_checkbox': speak_streaming_checkbox,
            'tts_rate': tts_rate,
            'tts_volume': tts_volume,
            'tts_mute': tts_mute,
            'voice_dropdown': voice_dropdown,
            'refresh_voices_btn': refresh_voices_btn,
            'test_tts_btn': test_tts_btn,
            'custom_text_input': custom_text_input,
            'speak_custom_btn': speak_custom_btn
        }
    
    def _build_memory_management(self):
        """Build memory management section"""
        save_memory_btn = gr.Button("Save Memory", size="sm")
        load_memory_file_input = gr.File(
            label="Load Memory File",
            file_types=[".json"]
        )
        load_memory_btn = gr.Button("Load Memory", size="sm")
        
        return {
            'save_memory_btn': save_memory_btn,
            'load_memory_file_input': load_memory_file_input,
            'load_memory_btn': load_memory_btn
        }
    
    def _build_footer(self):
        """Build footer section"""
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
    
    def _connect_events(self, chatbot, msg, send_btn, audio_output, status_output, components):
        """Connect all event handlers"""
        # Chat functionality
        msg.submit(
            self.handlers.chat_stream,
            inputs=[msg, chatbot],
            outputs=[chatbot, audio_output]
        ).then(lambda: "", outputs=msg)
        
        send_btn.click(
            self.handlers.chat_stream,
            inputs=[msg, chatbot],
            outputs=[chatbot, audio_output]
        ).then(lambda: "", outputs=msg)
        
        # Memory management
        self.clear_btn.click(
            self.handlers.clear_memory,
            outputs=[chatbot, status_output]
        )
        
        self.memory_status_btn.click(
            self.handlers.get_memory_status,
            outputs=status_output
        )
        
        components['save_memory_btn'].click(
            self.handlers.save_memory_file,
            outputs=components['model_status']
        )
        
        components['load_memory_btn'].click(
            self.handlers.load_memory_file,
            inputs=components['load_memory_file_input'],
            outputs=[chatbot, components['model_status']]
        )
        
        # TTS functionality
        self.speak_last_btn.click(
            self.handlers.speak_last_response,
            outputs=[audio_output, status_output]
        )
        
        components['test_tts_btn'].click(
            self.handlers.test_tts,
            outputs=[audio_output, components['model_status']]
        )
        
        components['speak_custom_btn'].click(
            self.handlers.speak_custom_text,
            inputs=components['custom_text_input'],
            outputs=[audio_output, components['model_status']]
        )
        
        components['voice_dropdown'].change(
            self.handlers.change_voice,
            inputs=components['voice_dropdown'],
            outputs=[components['voice_dropdown'], components['model_status']]
        )
        
        components['refresh_voices_btn'].click(
            self.handlers.refresh_voices,
            outputs=[components['voice_dropdown'], components['model_status']]
        )
        
        # TTS settings auto-update
        components['speak_streaming_checkbox'].change(
            self.handlers.toggle_speak_while_streaming,
            inputs=components['speak_streaming_checkbox'],
            outputs=components['model_status']
        )
        
        components['tts_rate'].change(
            self.handlers.update_speech_rate,
            inputs=components['tts_rate'],
            outputs=components['model_status']
        )
        
        components['tts_volume'].change(
            self.handlers.update_volume,
            inputs=components['tts_volume'],
            outputs=components['model_status']
        )
        
        components['tts_mute'].change(
            self.handlers.update_mute,
            inputs=components['tts_mute'],
            outputs=components['model_status']
        )
        
        # Model settings
        components['model_dropdown'].change(
            self.handlers.change_model,
            inputs=components['model_dropdown'],
            outputs=[components['current_model_display'], components['model_status']]
        )
        
        components['refresh_models_btn'].click(
            self.handlers.refresh_models,
            outputs=[components['model_dropdown'], components['current_model_display'], components['model_status']]
        )
        
        components['toggle_streaming_btn'].click(
            self.handlers.toggle_streaming,
            inputs=components['streaming_checkbox'],
            outputs=[components['streaming_checkbox'], components['model_status']]
        )
        
        # System prompt
        components['update_prompt_btn'].click(
            self.handlers.update_system_prompt,
            inputs=components['system_prompt'],
            outputs=status_output
        )