from datetime import datetime
from models.wordle_game import WordleGame
from typing import List

class AchievementSystem:
    ACHIEVEMENTS = {
        "speedster": {
            "name": "Blitzmeister ⚡",
            "condition": lambda game: game.get_duration() < 30,
            "description": "Gewinne ein Spiel in unter 30 Sekunden"
        },
        "perfectionist": {
            "name": "Perfektionist 🎯",
            "condition": lambda game: game.attempts == 1,
            "description": "Gewinne im ersten Versuch"
        },
        "hint_hater": {
            "name": "Tipp-Verweigerer 🙈",
            "condition": lambda game: game.hints_used == 0,
            "description": "Gewinne ohne Tipps"
        },
        "veteran": {
            "name": "Veteran 🏆",
            "condition": lambda count: count >= 100,
            "description": "Spiele 100 Spiele"
        }
    }

    def __init__(self, cog):
        self.cog = cog

    def check_achievements(self, user_id: int, game: WordleGame):
        self.cog.history.data.setdefault("achievements", {})
        
        user_achievements = self.cog.history.data["achievements"].setdefault(str(user_id), {})
        new_achievements = []
        
        total_games = len(self.cog.history.get_user_games(user_id, "global")) + len(
            self.cog.history.get_anonymous_games(
                self.cog.settings.get_settings(user_id)["anon_id"]
            )
        )
        
        for achievement_id, data in self.ACHIEVEMENTS.items():
            if achievement_id not in user_achievements:
                try:
                    if achievement_id == "veteran":
                        if data["condition"](total_games):  # 👈 Nur total_games übergeben
                            user_achievements[achievement_id] = datetime.now().isoformat()
                            new_achievements.append(data)
                    elif data["condition"](game):
                        user_achievements[achievement_id] = datetime.now().isoformat()
                        new_achievements.append(data)
                except Exception as e:
                    print(f"Achievement check error: {e}")
        
        return new_achievements
