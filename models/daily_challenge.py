from typing import Dict, Any, List
from datetime import datetime, timedelta
from models.database import Session, DailyChallenge

class DailyChallengeManager:
    def __init__(self):
        self.session = Session()
    
    def get_today_challenge(self) -> Dict[str, Any]:
        """Holt die heutige Challenge"""
        today = datetime.utcnow().date()
        challenge = self.session.query(DailyChallenge).filter(
            DailyChallenge.date >= today,
            DailyChallenge.date < today + timedelta(days=1)
        ).first()
        
        if not challenge:
            return None
        
        return {
            "date": challenge.date.isoformat(),
            "word": challenge.word,
            "participants": challenge.participants or {}
        }
    
    def create_challenge(self, word: str) -> None:
        """Erstellt eine neue Challenge"""
        today = datetime.utcnow().date()
        challenge = DailyChallenge(
            date=today,
            word=word,
            participants={}
        )
        self.session.add(challenge)
        self.session.commit()
    
    def add_participant(self, user_id: int, game_data: Dict[str, Any]) -> None:
        """Fügt einen Teilnehmer zur Challenge hinzu"""
        challenge = self.get_today_challenge()
        if not challenge:
            return
        
        participants = challenge["participants"]
        participants[str(user_id)] = game_data
        self.session.query(DailyChallenge).filter(
            DailyChallenge.date == datetime.fromisoformat(challenge["date"])
        ).update({"participants": participants})
        self.session.commit()
    
    def get_participants(self) -> Dict[str, Dict[str, Any]]:
        """Holt alle Teilnehmer der heutigen Challenge"""
        challenge = self.get_today_challenge()
        if not challenge:
            return {}
        return challenge["participants"]
    
    def get_user_challenge(self, user_id: int) -> Dict[str, Any]:
        """Holt die Challenge eines Benutzers"""
        challenge = self.get_today_challenge()
        if not challenge:
            return None
        return challenge["participants"].get(str(user_id))
    
    def has_participated(self, user_id: int) -> bool:
        """Prüft, ob ein Benutzer bereits teilgenommen hat"""
        return str(user_id) in self.get_participants()
    
    def get_all_challenges(self) -> List[Dict[str, Any]]:
        """Holt alle Challenges"""
        challenges = self.session.query(DailyChallenge).order_by(DailyChallenge.date.desc()).all()
        return [{
            "date": challenge.date.isoformat(),
            "word": challenge.word,
            "participants": challenge.participants or {}
        } for challenge in challenges]