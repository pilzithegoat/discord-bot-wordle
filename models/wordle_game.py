import random
import discord
from datetime import datetime
from utils.helpers import WORDS
from dotenv import load_dotenv

class WordleGame:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.secret_word = random.choice(WORDS)
        self.attempts = []
        self.remaining = MAX_ATTEMPTS
        self.hints_used = 0
        self.start_time = datetime.now()
        self.correct_positions = [False]*5
        self.hinted_letters = set()
    
    def get_duration(self):
        return (datetime.now() - self.start_time).total_seconds()
    
    def check_guess(self, guess: str) -> List[str]:
        secret = list(self.secret_word)
        result = [""]*5
        
        for i in range(5):
            if guess[i] == secret[i]:
                result[i] = "🟩"
                secret[i] = None
                self.correct_positions[i] = True
        
        for i in range(5):
            if result[i] == "🟩":
                continue
            if guess[i] in secret:
                result[i] = "🟨"
                secret[secret.index(guess[i])] = None
            else:
                result[i] = "⬛"
        
        self.attempts.append((guess.lower(), result.copy()))
        self.remaining -= 1
        return result
    
    def add_hint(self):
        if self.hints_used >= MAX_HINTS:
            return False
        available = [i for i, c in enumerate(self.correct_positions) if not c]
        if not available:
            return False
        pos = random.choice(available)
        self.hinted_letters.add(self.secret_word[pos])
        self.hints_used += 1
        return True
    
    @property
    def hint_display(self):
        return " ".join(c.upper() if c in self.hinted_letters or self.correct_positions[i] else "▢" 
                      for i, c in enumerate(self.secret_word))