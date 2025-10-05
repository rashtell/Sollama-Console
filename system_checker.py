import platform
import subprocess

from config import OLLAMA_INSTALL_SCRIPT, OLLAMA_MAC_URL, OLLAMA_WINDOWS_URL


class SystemChecker:
    """Checks system requirements and provides installation instructions"""
    
    @staticmethod
    def check_ollama_installation() -> bool:
        """Check if Ollama is installed and provide installation instructions"""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Ollama is installed")
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        SystemChecker._show_installation_instructions()
        return False
    
    @staticmethod
    def _show_installation_instructions():
        """Show detailed installation instructions for current OS"""
        print("❌ Ollama is not installed or not in PATH")
        print("\n" + "="*60)
        print("OLLAMA INSTALLATION INSTRUCTIONS")
        print("="*60)
        
        system = platform.system().lower()
        
        if system == "windows":
            SystemChecker._show_windows_instructions()
        elif system == "darwin":
            SystemChecker._show_macos_instructions()
        else:  # Linux
            SystemChecker._show_linux_instructions()
        
        SystemChecker._show_common_instructions()
    
    @staticmethod
    def _show_windows_instructions():
        print("\n🪟 WINDOWS INSTALLATION:")
        print(f"1. Download from: {OLLAMA_WINDOWS_URL}")
        print("2. Run OllamaSetup.exe installer")
        print("3. Ollama will start automatically in system tray")
        print("4. Open Command Prompt or PowerShell and run:")
        print("   ollama pull llama3.2")
        print("\nAlternative (if you have winget):")
        print("   winget install Ollama.Ollama")
    
    @staticmethod
    def _show_macos_instructions():
        print("\n🍎 MACOS INSTALLATION:")
        print(f"1. Download from: {OLLAMA_MAC_URL}")
        print("2. Drag Ollama.app to Applications folder")
        print("3. Launch Ollama from Applications")
        print("4. Open Terminal and run:")
        print("   ollama pull llama3.2")
        print("\nAlternative (if you have Homebrew):")
        print("   brew install ollama")
    
    @staticmethod
    def _show_linux_instructions():
        print("\n🐧 LINUX INSTALLATION:")
        print("1. Run the installation script:")
        print(f"   curl -fsSL {OLLAMA_INSTALL_SCRIPT} | sh")
        print("2. Start the service:")
        print("   sudo systemctl start ollama")
        print("   sudo systemctl enable ollama")
        print("3. Pull a model:")
        print("   ollama pull llama3.2")
        print("\nAlternative (manual):")
        print("   # Download binary from https://github.com/ollama/ollama/releases")
        print("   # Place in /usr/local/bin or /usr/bin")
    
    @staticmethod
    def _show_common_instructions():
        print("\n📋 AFTER INSTALLATION:")
        print("1. Verify installation: ollama --version")
        print("2. Test the model: ollama run llama3.2")
        print("3. Check API server: curl http://localhost:11434/api/tags")
        print("\n💡 RECOMMENDED MODELS TO TRY:")
        print("   ollama pull llama3.2        # Good balance (4.3GB)")
        print("   ollama pull llama3.2:1b     # Fastest, smaller (1.3GB)")
        print("   ollama pull mistral         # Alternative model (4.1GB)")
        print("   ollama pull codellama       # For coding tasks (3.8GB)")
        
        print("\n🔧 TROUBLESHOOTING:")
        print("- If 'connection refused': Run 'ollama serve' manually")
        print("- If slow responses: Try 'llama3.2:1b' model")
        print("- Check if running: netstat -an | grep 11434")
        print("- Windows: Check system tray for Ollama icon")
        print("="*60)

