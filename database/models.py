"""
資料模型定義
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# 筆記-標籤關聯表（多對多）
note_tags = Table(
    'note_tags',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# 筆記-筆記連結表（多對多，用於 [[]] 語法）
note_links = Table(
    'note_links',
    Base.metadata,
    Column('source_note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('target_note_id', Integer, ForeignKey('notes.id'), primary_key=True)
)

class User(Base):
    """用戶資料表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    ai_usage_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"

class Conversation(Base):
    """對話歷史表"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation(telegram_id={self.telegram_id}, role={self.role})>"

class Note(Base):
    """筆記表（支援 Graph View）"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    tags = relationship('Tag', secondary=note_tags, back_populates='notes')
    linked_to = relationship(
        'Note',
        secondary=note_links,
        primaryjoin=id == note_links.c.source_note_id,
        secondaryjoin=id == note_links.c.target_note_id,
        backref='linked_from'
    )
    
    def __repr__(self):
        return f"<Note(telegram_id={self.telegram_id}, title={self.title})>"

class Tag(Base):
    """標籤表"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    notes = relationship('Note', secondary=note_tags, back_populates='tags')
    
    def __repr__(self):
        return f"<Tag(name={self.name})>"

class UserSettings(Base):
    """用戶設定表"""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    language = Column(String(10), default='zh-TW')
    ai_persona = Column(String(50), default='assistant')
    notifications_enabled = Column(Boolean, default=True)
    timezone = Column(String(50), default='Asia/Taipei')
    
    def __repr__(self):
        return f"<UserSettings(telegram_id={self.telegram_id})>"