from datetime import datetime
from typing import Optional


class ConversationLogger:
    """Handles conversation logging to files"""
    
    def __init__(self, save_responses: bool = False):
        self.save_responses = save_responses
        self.conversation_file: Optional[str] = None
        self.question_count = 0
        
        if save_responses:
            self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Initialize conversation log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_file = f"ollama_conversation_{timestamp}.txt"
        
        with open(self.conversation_file, 'w', encoding='utf-8') as f:
            f.write(f"Ollama Conversation - {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
    
    def log_exchange(self, question: str, answer: str):
        """Log a question-answer exchange"""
        if not self.conversation_file:
            return
            
        self.question_count += 1
        try:
            with open(self.conversation_file, 'a', encoding='utf-8') as f:
                f.write(f"Q{self.question_count}: {question}\n")
                f.write(f"A{self.question_count}: {answer}\n\n")
        except Exception as e:
            print(f"Error saving conversation: {e}")

