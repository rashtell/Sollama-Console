"""Conversation memory management"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from config import DEFAULT_SYSTEM_PROMPT, DEFAULT_MAX_MEMORY


class ConversationMemory:
    """Manages conversation history and system prompts"""
    
    def __init__(self, system_prompt: Optional[str] = None, max_history: int = DEFAULT_MAX_MEMORY):
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = max_history
        self.memory_file: Optional[str] = None
        self.conversation_start_time = datetime.now()
    
    def add_exchange(self, user_message: str, assistant_response: str):
        """Add a user-assistant exchange to memory"""
        self.conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ])
        
        # Trim history if too long (keep system prompt + recent exchanges)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[2:]
    
    def get_full_context(self) -> List[Dict[str, str]]:
        """Get full conversation context including system prompt"""
        context = [{"role": "system", "content": self.system_prompt}]
        context.extend(self.conversation_history)
        return context
    
    def clear_history(self):
        """Clear conversation history but keep system prompt"""
        self.conversation_history = []
        self.conversation_start_time = datetime.now()
        print("🧹 Conversation memory cleared")
    
    def set_system_prompt(self, new_prompt: str):
        """Update the system prompt"""
        self.system_prompt = new_prompt
        print("🎭 System prompt updated")
    
    def get_memory_summary(self) -> str:
        """Get a summary of current memory state"""
        exchanges = len(self.conversation_history) // 2
        duration = datetime.now() - self.conversation_start_time
        
        summary = f"Memory: {exchanges} exchanges"
        if exchanges > 0:
            summary += f", {duration.total_seconds()/60:.1f}min session"
        
        return summary
    
    def save_memory(self, filepath: str) -> bool:
        """Save current memory to file"""
        try:
            memory_data = {
                "system_prompt": self.system_prompt,
                "conversation_history": self.conversation_history,
                "conversation_start_time": self.conversation_start_time.isoformat(),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Memory saved to: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save memory: {e}")
            return False
    
    def load_memory(self, filepath: str) -> bool:
        """Load memory from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            self.system_prompt = memory_data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
            self.conversation_history = memory_data.get("conversation_history", [])
            
            try:
                self.conversation_start_time = datetime.fromisoformat(
                    memory_data.get("conversation_start_time", datetime.now().isoformat())
                )
            except:
                self.conversation_start_time = datetime.now()
            
            exchanges = len(self.conversation_history) // 2
            print(f"📁 Memory loaded: {exchanges} previous exchanges")
            return True
            
        except FileNotFoundError:
            print(f"❌ Memory file not found: {filepath}")
            return False
        except Exception as e:
            print(f"❌ Failed to load memory: {e}")
            return False

