from typing import Optional, List, Dict, Any
from .database import Session, Guild, Word, Game
from datetime import datetime

WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

class ServerConfig:
    def __init__(self):
        self.session = Session()
    
    def __del__(self):
        self.session.close()
    
    def get_or_create_guild(self, guild_id: int, guild_name: str = None) -> Guild:
        guild = self.session.query(Guild).filter_by(id=guild_id).first()
        if not guild:
            guild = Guild(id=guild_id, name=guild_name)
            self.session.add(guild)
            self.session.commit()
        return guild
    
    def set_wordle_channel(self, guild_id: int, channel_id: int, guild_name: str = None):
        guild = self.get_or_create_guild(guild_id, guild_name)
        guild.wordle_channel = channel_id
        self.session.commit()
    
    def get_wordle_channel(self, guild_id: int) -> Optional[int]:
        guild = self.session.query(Guild).filter_by(id=guild_id).first()
        return guild.wordle_channel if guild else None
    
    def set_max_hints(self, guild_id: int, max_hints: int, guild_name: str = None):
        guild = self.get_or_create_guild(guild_id, guild_name)
        guild.max_hints = max_hints
        self.session.commit()
    
    def get_max_hints(self, guild_id: int) -> int:
        guild = self.session.query(Guild).filter_by(id=guild_id).first()
        return guild.max_hints if guild else 3
    
    def set_max_attempts(self, guild_id: int, max_attempts: int, guild_name: str = None):
        guild = self.get_or_create_guild(guild_id, guild_name)
        guild.max_attempts = max_attempts
        self.session.commit()
    
    def get_max_attempts(self, guild_id: int) -> int:
        guild = self.session.query(Guild).filter_by(id=guild_id).first()
        return guild.max_attempts if guild else 6
    
    def add_word(self, guild_id: int, word: str, guild_name: str = None):
        guild = self.get_or_create_guild(guild_id, guild_name)
        if not any(w.word == word for w in guild.words):
            new_word = Word(guild_id=guild_id, word=word)
            self.session.add(new_word)
            self.session.commit()
    
    def get_words(self, guild_id: int) -> List[str]:
        guild = self.session.query(Guild).filter_by(id=guild_id).first()
        return [w.word for w in guild.words] if guild else []
    
    def add_game_history(self, guild_id: int, game_data: Dict[str, Any], guild_name: str = None):
        guild = self.get_or_create_guild(guild_id, guild_name)
        game = Game(
            guild_id=guild_id,
            word=game_data["word"],
            winner_id=game_data["winner_id"],
            winner_name=game_data["winner_name"],
            attempts=game_data["attempts"],
            date=datetime.fromisoformat(game_data["date"])
        )
        self.session.add(game)
        self.session.commit()
    
    def get_game_history(self, guild_id: int) -> List[Dict[str, Any]]:
        guild = self.session.query(Guild).filter_by(id=guild_id).first()
        if not guild:
            return []
        
        return [{
            "word": game.word,
            "winner_id": game.winner_id,
            "winner_name": game.winner_name,
            "attempts": game.attempts,
            "date": game.date.isoformat()
        } for game in guild.games]
    
    def get_config(self, guild_id: int) -> Dict[str, Any]:
        """Holt die Konfiguration eines Servers"""
        guild = self.session.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            # Erstelle neue Konfiguration für den Server
            guild = Guild(
                id=guild_id,
                name="Unbekannt",
                wordle_channel=None,
                max_hints=3,
                max_attempts=6
            )
            self.session.add(guild)
            self.session.commit()
        
        return {
            "wordle_channel": guild.wordle_channel,
            "max_hints": guild.max_hints,
            "max_attempts": guild.max_attempts
        }
    
    def update_config(self, guild_id: int, **kwargs) -> None:
        """Aktualisiert die Konfiguration eines Servers"""
        guild = self.session.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            guild = Guild(id=guild_id)
            self.session.add(guild)
        
        for key, value in kwargs.items():
            if hasattr(guild, key):
                setattr(guild, key, value)
        
        self.session.commit()
    
    def delete_config(self, guild_id: int) -> None:
        """Löscht die Konfiguration eines Servers"""
        guild = self.session.query(Guild).filter(Guild.id == guild_id).first()
        if guild:
            self.session.delete(guild)
            self.session.commit()
    
    def get_all_configs(self) -> Dict[int, Dict[str, Any]]:
        """Holt alle Server-Konfigurationen"""
        guilds = self.session.query(Guild).all()
        return {
            guild.id: {
                "wordle_channel": guild.wordle_channel,
                "max_hints": guild.max_hints,
                "max_attempts": guild.max_attempts
            }
            for guild in guilds
        }