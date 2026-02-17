import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 取得資料庫 URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    # Railway 的新版本使用 postgresql://
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# 創建資料庫引擎
engine = None
SessionLocal = None
Base = declarative_base()

def init_db():
    """初始化資料庫連線"""
    global engine, SessionLocal
    
    if not DATABASE_URL:
        logger.warning("⚠️ DATABASE_URL 未設置，資料庫功能將無法使用")
        return False
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        
        # 創建所有表格
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ 資料庫連線成功")
        return True
    except Exception as e:
        logger.error(f"❌ 資料庫連線失敗: {e}")
        return False

def get_db():
    """取得資料庫 session"""
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"資料庫 session 錯誤: {e}")
        return None

# ==================== 資料表定義 ====================

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

class Conversation(Base):
    """對話歷史表"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Note(Base):
    """筆記表"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserSettings(Base):
    """用戶設定表"""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    language = Column(String(10), default='zh-TW')
    ai_persona = Column(String(50), default='assistant')
    notifications_enabled = Column(Boolean, default=True)
    timezone = Column(String(50), default='Asia/Taipei')

# ==================== 資料庫操作函數 ====================

def get_or_create_user(telegram_id: int, username: str = None, 
                       first_name: str = None, last_name: str = None):
    """取得或創建用戶"""
    db = get_db()
    if db is None:
        return None
    
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user is None:
            # 創建新用戶
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✅ 新用戶創建: {telegram_id}")
        else:
            # 更新最後活動時間
            user.last_active = datetime.utcnow()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            db.commit()
        
        return user
    except Exception as e:
        logger.error(f"get_or_create_user 錯誤: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def increment_message_count(telegram_id: int):
    """增加訊息計數"""
    db = get_db()
    if db is None:
        return
    
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.message_count += 1
            db.commit()
    except Exception as e:
        logger.error(f"increment_message_count 錯誤: {e}")
        db.rollback()
    finally:
        db.close()

def increment_ai_usage(telegram_id: int):
    """增加 AI 使用計數"""
    db = get_db()
    if db is None:
        return
    
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.ai_usage_count += 1
            db.commit()
    except Exception as e:
        logger.error(f"increment_ai_usage 錯誤: {e}")
        db.rollback()
    finally:
        db.close()

def save_conversation(telegram_id: int, role: str, content: str):
    """儲存對話"""
    db = get_db()
    if db is None:
        return
    
    try:
        conversation = Conversation(
            telegram_id=telegram_id,
            role=role,
            content=content
        )
        db.add(conversation)
        db.commit()
    except Exception as e:
        logger.error(f"save_conversation 錯誤: {e}")
        db.rollback()
    finally:
        db.close()

def get_conversation_history(telegram_id: int, limit: int = 10):
    """取得對話歷史"""
    db = get_db()
    if db is None:
        return []
    
    try:
        conversations = db.query(Conversation).filter(
            Conversation.telegram_id == telegram_id
        ).order_by(
            Conversation.created_at.desc()
        ).limit(limit).all()
        
        # 反轉順序（最舊的在前）
        return list(reversed(conversations))
    except Exception as e:
        logger.error(f"get_conversation_history 錯誤: {e}")
        return []
    finally:
        db.close()

def clear_conversation_history(telegram_id: int):
    """清除對話歷史"""
    db = get_db()
    if db is None:
        return False
    
    try:
        db.query(Conversation).filter(
            Conversation.telegram_id == telegram_id
        ).delete()
        db.commit()
        return True
    except Exception as e:
        logger.error(f"clear_conversation_history 錯誤: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def save_note(telegram_id: int, title: str, content: str):
    """儲存筆記"""
    db = get_db()
    if db is None:
        return None
    
    try:
        note = Note(
            telegram_id=telegram_id,
            title=title,
            content=content
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        logger.error(f"save_note 錯誤: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def get_user_notes(telegram_id: int):
    """取得用戶所有筆記"""
    db = get_db()
    if db is None:
        return []
    
    try:
        notes = db.query(Note).filter(
            Note.telegram_id == telegram_id
        ).order_by(
            Note.created_at.desc()
        ).all()
        return notes
    except Exception as e:
        logger.error(f"get_user_notes 錯誤: {e}")
        return []
    finally:
        db.close()

def delete_note(telegram_id: int, note_id: int):
    """刪除筆記"""
    db = get_db()
    if db is None:
        return False
    
    try:
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.telegram_id == telegram_id
        ).first()
        
        if note:
            db.delete(note)
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"delete_note 錯誤: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_user_stats(telegram_id: int):
    """取得用戶統計"""
    db = get_db()
    if db is None:
        return None
    
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            note_count = db.query(Note).filter(Note.telegram_id == telegram_id).count()
            conversation_count = db.query(Conversation).filter(
                Conversation.telegram_id == telegram_id
            ).count()
            
            return {
                'message_count': user.message_count,
                'ai_usage_count': user.ai_usage_count,
                'note_count': note_count,
                'conversation_count': conversation_count,
                'created_at': user.created_at,
                'last_active': user.last_active
            }
        return None
    except Exception as e:
        logger.error(f"get_user_stats 錯誤: {e}")
        return None
    finally:
        db.close()
