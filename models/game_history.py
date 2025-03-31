import json
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict
from models.user_settings import UserSettings
from models.server_config import ServerConfig

class GameHistory:
    def __init__(self):
        self.data = self.load_data()
    
    def load_data(self):
        try:
            with open(DATA_FILE) as f:
                return self.validate_data_structure(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return self.default_data_structure()
    
    def validate_data_structure(self, data):
        data.setdefault("guilds", {})
        data.setdefault("global", {"users": {}})
        data.setdefault("anonymous_games", {})
        data.setdefault("achievements", {})
        data.setdefault("daily_challenges", {}) 
        
        # Migration für alte Datensätze
        for scope in [data["global"], *data["guilds"].values()]:
            for user_games in scope.get("users", {}).values():
                for game in user_games:
                    game.setdefault("id", str(uuid.uuid4())[:8].upper())
                    game.setdefault("anonymous", False)
    
        for anon_games in data["anonymous_games"].values():
            for game in anon_games:
                game.setdefault("id", str(uuid.uuid4())[:8].upper())
                game.setdefault("anonymous", True)
    
        return data
    
    def default_data_structure(self):
        return {"guilds": {}, 
                "global": {"users": {}}, 
                "anonymous_games": {},
                "achievements": {},
                "daily_challenges": {}
                }
    
    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def add_game(self, guild_id: int, user_id: int, game_data: dict):
        settings = UserSettings().get_settings(user_id)
    
        game_entry = {
        "id": str(uuid.uuid4())[:8].upper(),
        "timestamp": datetime.now().isoformat(),
        "won": game_data["won"],
        "word": game_data["word"],
        "attempts": len(game_data["guesses"]),
        "hints": game_data["hints"],
        "guesses": [{"word": g[0], "result": g[1]} for g in game_data["guesses"]],
        "duration": game_data["duration"],
        "anonymous": settings["anonymous"],
        "guild_id": guild_id  # 👈 Füge guild_id für alle Spiele hinzu
        }
    
        if settings["anonymous"]:
            anon_id = settings["anon_id"]
            self.data["anonymous_games"].setdefault(anon_id, []).insert(0, game_entry)
            settings["anon_games"].insert(0, game_entry["id"])
            UserSettings().update_settings(user_id, anon_games=settings["anon_games"])
        else:
            guild_str = str(guild_id)
            user_str = str(user_id)
            self.data["guilds"].setdefault(guild_str, {"users": {}})
            self.data["guilds"][guild_str]["users"].setdefault(user_str, []).insert(0, game_entry)
            self.data["global"]["users"].setdefault(user_str, []).insert(0, game_entry)
    
        self.save_data()
    
    def get_leaderboard(self, scope: str, guild_id: Optional[int] = None) -> List[dict]:
        source = self.data["global"] if scope == "global" else self.data["guilds"].get(str(guild_id), {"users": {}})
        leaderboard = []
        for user_id_str, games in source["users"].items():
            valid_games = [g for g in games if not g.get("anonymous", False)]
            total = len(valid_games)
            if total == 0:
                continue
            wins = sum(g["won"] for g in valid_games)
            avg_attempts = sum(g["attempts"] for g in valid_games) / total
            win_rate = wins / total
            last_games = sorted(valid_games[:10], key=lambda x: x["timestamp"], reverse=True)
            leaderboard.append({
                "user_id": int(user_id_str),
                "wins": wins,
                "total": total,
                "avg_attempts": avg_attempts,
                "win_rate": win_rate,
                "last_games": last_games
            })
        return sorted(leaderboard, key=lambda x: (-x["wins"], -x["total"]))
    
    def get_user_games(self, user_id: int, scope: str, guild_id: Optional[int] = None) -> List[dict]:
        source = self.data["global"] if scope == "global" else self.data["guilds"].get(str(guild_id), {"users": {}})
        return source["users"].get(str(user_id), [])
    
    def get_anonymous_games(self, anon_id: str) -> List[dict]:
        return self.data["anonymous_games"].get(anon_id, [])