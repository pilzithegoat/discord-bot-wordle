from typing import Dict, Any, List
from datetime import datetime
from models.database import Session, Achievement

class AchievementSystem:
    def __init__(self):
        self.session = Session()
    
    def add_achievement(self, user_id: int, achievement_type: str) -> None:
        """Fügt ein Achievement hinzu"""
        achievement = Achievement(
            user_id=user_id,
            achievement_type=achievement_type,
            unlocked_at=datetime.utcnow()
        )
        self.session.add(achievement)
        self.session.commit()
    
    def get_user_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Holt alle Achievements eines Benutzers"""
        achievements = self.session.query(Achievement).filter(
            Achievement.user_id == user_id
        ).order_by(Achievement.unlocked_at.desc()).all()
        
        return [{
            "type": achievement.achievement_type,
            "unlocked_at": achievement.unlocked_at.isoformat()
        } for achievement in achievements]
    
    def has_achievement(self, user_id: int, achievement_type: str) -> bool:
        """Prüft, ob ein Benutzer ein bestimmtes Achievement hat"""
        return self.session.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.achievement_type == achievement_type
        ).first() is not None
    
    def get_all_achievements(self) -> Dict[int, List[Dict[str, Any]]]:
        """Holt alle Achievements aller Benutzer"""
        achievements = self.session.query(Achievement).order_by(
            Achievement.unlocked_at.desc()
        ).all()
        
        result = {}
        for achievement in achievements:
            if achievement.user_id not in result:
                result[achievement.user_id] = []
            result[achievement.user_id].append({
                "type": achievement.achievement_type,
                "unlocked_at": achievement.unlocked_at.isoformat()
            })
        
        return result
