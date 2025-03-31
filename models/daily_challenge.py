import json
import random
from datetime import datetime
from utils.helpers import WORDS
from typing import Optional, List, Dict, Any

class DailyChallenge:
    def __init__(self):
        self.data = self.load_data()
    
    def load_data(self):
        try:
            with open(DAILY_FILE) as f:
                data = json.load(f)
                data["last_updated"] = datetime.strptime(data["last_updated"], "%Y-%m-%d").date()
                return data
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            return {
                "current_word": None,
                "last_updated": None,
                "participants": {}
            }
    
    def save_data(self):
        with open(DAILY_FILE, "w") as f:
            save_data = self.data.copy()
            save_data["last_updated"] = self.data["last_updated"].isoformat()
            json.dump(save_data, f, indent=2)
    
    def get_daily_word(self):
        if self.should_reset():
            self.data["current_word"] = random.choice(WORDS)
            self.data["last_updated"] = datetime.now().date()
            self.data["participants"] = {}
            self.save_data()
        return self.data["current_word"]
    
    def should_reset(self):
        return self.data["last_updated"] != datetime.now().date()
    
    def has_played(self, user_id: int):
        return str(user_id) in self.data["participants"]
    
    def add_participant(self, user_id: int, attempts: int):
        self.data["participants"][str(user_id)] = {
            "attempts": attempts,
            "timestamp": datetime.now().isoformat()
        }
        self.save_data()