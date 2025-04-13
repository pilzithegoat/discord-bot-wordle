import json
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict
from models.user_settings import UserSettings
from models.server_config import ServerConfig
from typing import Optional, List, Dict
from models.database import Session, Game

WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

class GameHistory:
    def __init__(self):
        self.session = Session()
    
    def add_game(self, guild_id: int, user_id: int, game_data: dict):
        """Fügt ein neues Spiel zur Historie hinzu"""
        game = Game(
            game_id=game_data.get('id', str(uuid.uuid4().hex[:8].upper())),
            guild_id=guild_id,
            user_id=user_id,
            word=game_data['word'],
            won=game_data['won'],
            attempts=len(game_data['guesses']),
            hints_used=game_data['hints'],
            duration=int(game_data['duration']),
            anonymous=game_data.get('anonymous', False),
            timestamp=datetime.fromisoformat(game_data['timestamp']) if 'timestamp' in game_data else datetime.utcnow(),
            guesses=game_data['guesses']
        )
        self.session.add(game)
        self.session.commit()
    
    def get_user_games(self, user_id: int, scope="global"):
        """Holt alle Spiele eines Benutzers"""
        query = self.session.query(Game).filter(
            Game.user_id == user_id,
            Game.anonymous == False
        )
        
        if scope != "global":
            query = query.filter(Game.guild_id == int(scope))
        
        games = query.order_by(Game.timestamp.desc()).all()
        
        return [{
            'id': game.game_id,
            'timestamp': game.timestamp.isoformat(),
            'won': game.won,
            'word': game.word,
            'attempts': game.attempts,
            'hints': game.hints_used,
            'guesses': game.guesses,
            'duration': game.duration,
            'anonymous': game.anonymous,
            'guild_id': game.guild_id
        } for game in games]
    
    def get_anonymous_games(self, anon_id: str):
        """Holt alle anonymen Spiele eines Benutzers"""
        games = self.session.query(Game).filter(
            Game.anonymous == True
        ).order_by(Game.timestamp.desc()).all()
        
        return [{
            'id': game.game_id,
            'timestamp': game.timestamp.isoformat(),
            'won': game.won,
            'word': game.word,
            'attempts': game.attempts,
            'hints': game.hints_used,
            'guesses': game.guesses,
            'duration': game.duration,
            'anonymous': game.anonymous,
            'guild_id': game.guild_id
        } for game in games]

    def get_guild_games(self, guild_id: int):
        """Holt alle Spiele eines Servers"""
        games = self.session.query(Game).filter(
            Game.guild_id == guild_id,
            Game.anonymous == False
        ).order_by(Game.timestamp.desc()).all()
        
        return [{
            'id': game.game_id,
            'timestamp': game.timestamp.isoformat(),
            'won': game.won,
            'word': game.word,
            'attempts': game.attempts,
            'hints': game.hints_used,
            'guesses': game.guesses,
            'duration': game.duration,
            'anonymous': game.anonymous,
            'guild_id': game.guild_id
        } for game in games]

    def get_global_games(self):
        """Holt alle öffentlichen Spiele"""
        games = self.session.query(Game).filter(
            Game.anonymous == False
        ).order_by(Game.timestamp.desc()).all()
        
        return [{
            'id': game.game_id,
            'timestamp': game.timestamp.isoformat(),
            'won': game.won,
            'word': game.word,
            'attempts': game.attempts,
            'hints': game.hints_used,
            'guesses': game.guesses,
            'duration': game.duration,
            'anonymous': game.anonymous,
            'guild_id': game.guild_id
        } for game in games]