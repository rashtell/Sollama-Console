# Sollama - Python Version with Memory

A modular Python application for conversational AI with Ollama, featuring text-to-speech, conversation memory, and streaming responses.

## Architecture Overview

The application has been refactored into a clean, modular architecture with clear separation of concerns:

### Core Modules

- **`config.py`** - Central configuration and constants
- **`main.py`** - Entry point with argument parsing
- **`sollama_app.py`** - Main application orchestrator

### Component Modules

- **`memory_manager.py`** - Conversation history and context management
- **`tts_manager.py`** - Text-to-speech functionality with threading
- **`ollama_client.py`** - Ollama API communication and streaming
- **`system_checker.py`** - Installation verification and setup guidance
- **`command_handler.py`** - Interactive command processing and help system
- **`conversation_logger.py`** - File-based conversation logging

## Installation Requirements

1. Ollama (AI model server)
2. Python TTS library (pyttsx3 or pywin32)

## Ollama Installation

### Windows

1. Download from: <https://ollama.ai/download/windows>
2. Run the installer (OllamaSetup.exe)
3. Ollama will start automatically
4. Open Command Prompt and run: `ollama pull llama3.2`

### macOS

1. Download from: <https://ollama.ai/download/mac>
2. Drag Ollama.app to Applications folder
3. Run Ollama from Applications
4. Open Terminal and run: `ollama pull llama3.2`

### Linux

1. Run: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Start service: `sudo systemctl start ollama`
3. Pull model: `ollama pull llama3.2`

## Python TTS Installation

- **Windows:** `pip install pyttsx3`
- **Linux/Mac:** `pip install pyttsx3`

## Installation & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify Ollama installation
ollama --version
ollama run llama3.2

# Check server
curl http://localhost:11434/api/tags
```

## Verify Installation

1. Check Ollama: `ollama --version`
2. Test model: `ollama run llama3.2`
3. Check server: `curl http://localhost:11434/api/tags`

## Troubleshooting

- **If "connection refused":** Run `ollama serve` manually
- **If no TTS:** Install with `pip install pyttsx3`
- **If slow responses:** Try smaller model like `llama3.2:1b`

## Command Line Usage

### Basic Usage

```bash
# Run with default settings
python main.py
```

### Common Options

```bash
python main.py --model llama3.2:1b --volume 0.5
python main.py --mute --system-prompt "You are a coding expert"
python main.py --load-memory my_session.json
```

### All Command Line Arguments

| Argument                    | Description                                  |
| --------------------------- | -------------------------------------------- |
| `-m, --model MODEL`         | Ollama model (default: llama3.2)             |
| `-u, --url URL`             | Server URL (default: <http://localhost:11434>) |
| `-r, --rate RATE`           | Speech rate 50-300 (default: 175)            |
| `-v, --volume VOLUME`       | Volume 0.0-1.0 (default: 1.0)                |
| `--mute`                    | Start with audio muted                       |
| `-s, --save`                | Save conversation to timestamped file        |
| `-sp, --system-prompt TEXT` | Custom system prompt for assistant           |
| `-mm, --max-memory NUM`     | Max conversation exchanges (default: 50)     |
| `-lm, --load-memory FILE`   | Load previous conversation memory            |

### Examples

```bash
python main.py --volume 0.3 --rate 200
python main.py --mute --model mistral
python main.py --system-prompt "You are a creative writing coach"
python main.py --load-memory conversation_20240825.json
```

## Features

### Core Features

- **Conversation memory:** Assistant remembers previous exchanges
- **System prompts:** Configure assistant personality/behavior
- **Memory management:** Clear, save, and load conversation history
- **Enhanced audio:** Mute, precise volume control, command line audio settings
- **Enhanced context:** Better multi-turn conversations

### Technical Features

- **Streaming responses:** Real-time response generation
- **Live TTS:** Text-to-speech during streaming
- **Multiple TTS engines:** Support for pyttsx3 and SAPI
- **Voice selection:** Choose from available system voices
- **Persistent memory:** Save and load conversation sessions

## Interactive Commands

| Command              | Description                      |
| -------------------- | -------------------------------- |
| `exit/quit/bye`      | Exit the program                 |
| `clear/new/reset`    | Clear conversation memory        |
| `memory`             | Show memory status               |
| `system <prompt>`    | Set system prompt                |
| `save_memory [file]` | Save conversation memory         |
| `load_memory <file>` | Load conversation memory         |
| `models`             | List available models            |
| `model <name>`       | Switch to different model        |
| `repeat`             | Repeat last response             |
| `test_tts`           | Test TTS functionality           |
| `voice`              | List available voices            |
| `voice <number>`     | Switch to voice number           |
| `faster/slower`      | Adjust speech speed              |
| `louder/quieter`     | Adjust volume by 0.1             |
| `volume <0.0-1.0>`   | Set specific volume level        |
| `mute/unmute`        | Mute or unmute audio             |
| `stream`             | Toggle streaming mode on/off     |
| `live_tts`           | Toggle live TTS during streaming |
| `help`               | Show interactive help            |
| `<question>`         | Ask ollama a question            |

## Module Dependencies

```
main.py
├── sollama_app.py
│   ├── memory_manager.py
│   ├── tts_manager.py
│   ├── ollama_client.py
│   ├── system_checker.py
│   ├── command_handler.py
│   └── conversation_logger.py
└── config.py
```

## Architecture Benefits

### Key Improvements

#### Separation of Concerns

- Each module has a single, well-defined responsibility
- Clear interfaces between components
- Reduced coupling and improved testability

#### Enhanced Maintainability

- Smaller, focused classes and methods
- Better error handling and logging
- Consistent naming conventions

#### Improved Extensibility

- Easy to add new TTS engines
- Simple to extend command system
- Modular architecture supports new features

### Benefits of Refactoring

1. **Modularity**: Each component can be developed, tested, and maintained independently
2. **Reusability**: Components can be reused in other projects
3. **Testability**: Smaller modules are easier to unit test
4. **Maintainability**: Changes to one component don't affect others
5. **Readability**: Code is easier to understand and navigate
6. **Extensibility**: New features can be added without modifying existing code

## File Structure

```
sollama/
├── main.py                    # Entry point
├── config.py                  # Configuration constants
├── sollama_app.py             # Main application class
├── memory_manager.py          # Conversation memory
├── tts_manager.py             # Text-to-speech handling
├── ollama_client.py           # Ollama API client
├── system_checker.py          # Installation verification
├── command_handler.py         # Interactive commands
├── conversation_logger.py     # File logging
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Future Enhancements

The modular structure makes it easy to add:

- Multiple TTS engine support
- Different AI model backends
- Web interface components
- Database persistence
- Plugin systems
- API endpoints
- Multi-language support
- Custom voice training
- Advanced memory strategies

## Development

### Adding New Commands

1. Add command handling logic to `command_handler.py`
2. Update help text in `show_help()` method
3. Test the new functionality

### Adding New TTS Engines

1. Extend `TTSManager` class in `tts_manager.py`
2. Add engine detection in initialization
3. Implement engine-specific methods

### Extending Memory System

1. Modify `ConversationMemory` class in `memory_manager.py`
2. Add new persistence formats
3. Implement advanced context strategies

## Contributing

The modular architecture makes contributions straightforward:

1. Identify the relevant module for your changes
2. Follow existing patterns and naming conventions
3. Add appropriate error handling
4. Update documentation as needed
5. Test your changes in isolation

## License

[Add your license information here]
