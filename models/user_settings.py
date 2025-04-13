import json
import os
from typing import Dict, Any
from models.database import Session, UserSettings
from datetime import datetime

WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

class UserSettingsManager:
    def __init__(self):
        self.session = Session()
    
    def get_settings(self, user_id: int) -> Dict[str, Any]:
        """Holt die Einstellungen eines Benutzers"""
        settings = self.session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            # Erstelle neue Einstellungen für den Benutzer
            settings = UserSettings(
                user_id=user_id,
                stats_public=True,
                history_public=True,
                anonymous=False,
                anon_password=None
            )
            self.session.add(settings)
            self.session.commit()
        
        return {
            "stats_public": settings.stats_public,
            "history_public": settings.history_public,
            "anonymous": settings.anonymous,
            "anon_password": settings.anon_password
        }
    
    def update_settings(self, user_id: int, **kwargs) -> None:
        """Aktualisiert die Einstellungen eines Benutzers"""
        settings = self.session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            self.session.add(settings)
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        self.session.commit()
    
    def delete_settings(self, user_id: int) -> None:
        """Löscht die Einstellungen eines Benutzers"""
        settings = self.session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings:
            self.session.delete(settings)
            self.session.commit()
