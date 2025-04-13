from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Guild(Base):
    __tablename__ = 'guilds'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    wordle_channel = Column(Integer)
    max_hints = Column(Integer, default=3)
    max_attempts = Column(Integer, default=6)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    words = relationship("Word", back_populates="guild")
    games = relationship("Game", back_populates="guild")

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    word = Column(String(5), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    guild = relationship("Guild", back_populates="words")

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True)  # For the unique game ID like "FB800E26"
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(Integer, nullable=False)
    word = Column(String(5), nullable=False)
    won = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)
    duration = Column(Integer)  # Duration in seconds
    anonymous = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    guesses = Column(JSON)  # Store the guesses and their results as JSON
    
    guild = relationship("Guild", back_populates="games")

class Achievement(Base):
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    achievement_type = Column(String, nullable=False)  # e.g., "speedster", "hint_hater"
    unlocked_at = Column(DateTime, default=datetime.utcnow)

class DailyChallenge(Base):
    __tablename__ = 'daily_challenges'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    word = Column(String(5), nullable=False)
    participants = Column(JSON)  # Store participant data as JSON

class UserSettings(Base):
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    stats_public = Column(Boolean, default=True)
    history_public = Column(Boolean, default=True)
    anonymous = Column(Boolean, default=False)
    anon_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create database engine
engine = create_engine('sqlite:///wordle.db')
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine) 