"""
資料庫 CRUD 操作
"""
from typing import Optional, List, Dict
from datetime import datetime
from database.connection import db_manager
from database.models import User, Conversation, Note, UserSettings
from utils.logger import setup_logger
from database.models import User, Conversation, Note, UserSettings, Tag, note_tags, note_links
import re

logger = setup_logger(__name__)

# ==================== User 操作 ====================

def get_or_create_user(telegram_id: int, username: str = None,
                      first_name: str = None, last_name: str = None) -> Optional[User]:
    """取得或創建用戶"""
    with db_manager.get_session() as session:
        if session is None:
            return None
        
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            logger.info(f"✅ 新用戶創建: {telegram_id}")
        else:
            # 更新資訊
            user.last_active = datetime.utcnow()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
        
        session.flush()
        session.refresh(user)
        return user

def increment_message_count(telegram_id: int) -> bool:
    """增加訊息計數"""
    with db_manager.get_session() as session:
        if session is None:
            return False
        
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.message_count += 1
            return True
        return False

def increment_ai_usage(telegram_id: int) -> bool:
    """增加 AI 使用計數"""
    with db_manager.get_session() as session:
        if session is None:
            return False
        
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.ai_usage_count += 1
            return True
        return False

def get_user_stats(telegram_id: int) -> Optional[Dict]:
    """取得用戶統計"""
    with db_manager.get_session() as session:
        if session is None:
            return None
        
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return None
        
        note_count = session.query(Note).filter(Note.telegram_id == telegram_id).count()
        conversation_count = session.query(Conversation).filter(
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

# ==================== Conversation 操作 ====================

def save_conversation(telegram_id: int, role: str, content: str) -> bool:
    """儲存對話"""
    with db_manager.get_session() as session:
        if session is None:
            return False
        
        conversation = Conversation(
            telegram_id=telegram_id,
            role=role,
            content=content
        )
        session.add(conversation)
        return True
    
def get_conversation_history(telegram_id: int, limit: int = 10) -> List[Dict]:
    """
    取得對話歷史
    
    Returns:
        字典列表，包含 role, content, created_at
    """
    with db_manager.get_session() as session:
        if session is None:
            return []
        
        try:
            conversations = session.query(Conversation).filter(
                Conversation.telegram_id == telegram_id
            ).order_by(
                Conversation.created_at.desc()
            ).limit(limit).all()
            
            # 在 session 關閉前轉換為字典（避免 DetachedInstanceError）
            result = []
            for conv in reversed(conversations):  # 反轉順序，最舊的在前
                result.append({
                    'role': conv.role,
                    'content': conv.content,
                    'created_at': conv.created_at
                })
            
            return result
        
        except Exception as e:
            logger.error(f"get_conversation_history 錯誤: {e}")
            return []
           
def clear_conversation_history(telegram_id: int) -> bool:
    """清除對話歷史"""
    with db_manager.get_session() as session:
        if session is None:
            return False
        
        try:
            count = session.query(Conversation).filter(
                Conversation.telegram_id == telegram_id
            ).delete()
            logger.info(f"清除了 {count} 條對話記錄（用戶 {telegram_id}）")
            return True
        except Exception as e:
            logger.error(f"clear_conversation_history 錯誤: {e}")
            return False
        
# ==================== Note 操作 ====================

def save_note(telegram_id: int, title: str, content: str) -> Optional[Note]:
    """儲存筆記"""
    with db_manager.get_session() as session:
        if session is None:
            return None
        
        note = Note(
            telegram_id=telegram_id,
            title=title,
            content=content
        )
        session.add(note)
        session.flush()
        session.refresh(note)
        return note

def get_user_notes(telegram_id: int) -> List[Dict]:
    """
    取得用戶所有筆記
    
    Returns:
        字典列表，包含 id, title, content, created_at
    """
    with db_manager.get_session() as session:
        if session is None:
            return []
        
        try:
            notes = session.query(Note).filter(
                Note.telegram_id == telegram_id
            ).order_by(
                Note.created_at.desc()
            ).all()
            
            # 轉換為字典
            result = []
            for note in notes:
                result.append({
                    'id': note.id,
                    'title': note.title,
                    'content': note.content,
                    'created_at': note.created_at,
                    'updated_at': note.updated_at
                })
            
            return result
        
        except Exception as e:
            logger.error(f"get_user_notes 錯誤: {e}")
            return []
        
def delete_note(telegram_id: int, note_id: int) -> bool:
    """刪除筆記"""
    with db_manager.get_session() as session:
        if session is None:
            return False
        
        note = session.query(Note).filter(
            Note.id == note_id,
            Note.telegram_id == telegram_id
        ).first()
        
        if note:
            session.delete(note)
            return True
        return False
    
# ==================== Tag 操作 ====================

def get_or_create_tag(telegram_id: int, tag_name: str):
    """取得或創建標籤"""
    with db_manager.get_session() as session:
        if session is None:
            return None
        
        try:
            tag = session.query(Tag).filter(
                Tag.telegram_id == telegram_id,
                Tag.name == tag_name
            ).first()
            
            if tag is None:
                tag = Tag(telegram_id=telegram_id, name=tag_name)
                session.add(tag)
                session.flush()
            
            return tag
        except Exception as e:
            logger.error(f"get_or_create_tag 錯誤: {e}")
            return None

def extract_tags(content: str) -> List[str]:
    """從內容中提取標籤（#標籤 格式）"""
    # 匹配 #標籤 格式
    tags = re.findall(r'#(\w+)', content)
    return list(set(tags))  # 去重

def extract_links(content: str) -> List[str]:
    """從內容中提取連結（[[筆記標題]] 格式）"""
    # 匹配 [[筆記標題]] 格式
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    return links

def save_note_with_metadata(telegram_id: int, title: str, content: str) -> Optional[Dict]:
    """
    儲存筆記（支援標籤和連結）
    
    Returns:
        包含筆記資訊的字典
    """
    with db_manager.get_session() as session:
        if session is None:
            return None
        
        try:
            # 創建筆記
            note = Note(
                telegram_id=telegram_id,
                title=title,
                content=content
            )
            session.add(note)
            session.flush()  # 取得 note.id
            
            # 提取並添加標籤
            tag_names = extract_tags(content)
            for tag_name in tag_names:
                tag = session.query(Tag).filter(
                    Tag.telegram_id == telegram_id,
                    Tag.name == tag_name
                ).first()
                
                if tag is None:
                    tag = Tag(telegram_id=telegram_id, name=tag_name)
                    session.add(tag)
                
                note.tags.append(tag)
            
            # 提取並添加連結
            link_titles = extract_links(content)
            for link_title in link_titles:
                # 找到目標筆記
                target_note = session.query(Note).filter(
                    Note.telegram_id == telegram_id,
                    Note.title == link_title
                ).first()
                
                if target_note:
                    note.linked_to.append(target_note)
            
            session.flush()
            session.refresh(note)
            
            # 返回筆記資訊
            return {
                'id': note.id,
                'title': note.title,
                'content': note.content,
                'tags': [tag.name for tag in note.tags],
                'links': [n.title for n in note.linked_to],
                'created_at': note.created_at
            }
        
        except Exception as e:
            logger.error(f"save_note_with_metadata 錯誤: {e}")
            return None

def get_note_graph_data(telegram_id: int) -> Dict:
    """
    取得用戶的筆記圖譜資料
    
    Returns:
        包含 nodes 和 edges 的字典
    """
    with db_manager.get_session() as session:
        if session is None:
            return {"nodes": [], "edges": []}
        
        try:
            # 取得所有筆記
            notes = session.query(Note).filter(
                Note.telegram_id == telegram_id
            ).all()
            
            nodes = []
            edges = []
            
            # 構建節點
            for note in notes:
                nodes.append({
                    'id': note.id,
                    'title': note.title,
                    'tags': [tag.name for tag in note.tags],
                    'created_at': note.created_at.isoformat()
                })
                
                # 構建連結邊
                for linked_note in note.linked_to:
                    edges.append({
                        'source': note.id,
                        'target': linked_note.id,
                        'type': 'link'
                    })
            
            # 添加基於標籤的邊
            tag_groups = {}
            for note in notes:
                for tag in note.tags:
                    if tag.name not in tag_groups:
                        tag_groups[tag.name] = []
                    tag_groups[tag.name].append(note.id)
            
            # 為同標籤的筆記創建邊
            for tag_name, note_ids in tag_groups.items():
                for i, source_id in enumerate(note_ids):
                    for target_id in note_ids[i+1:]:
                        edges.append({
                            'source': source_id,
                            'target': target_id,
                            'type': 'tag',
                            'tag': tag_name
                        })
            
            return {
                'nodes': nodes,
                'edges': edges
            }
        
        except Exception as e:
            logger.error(f"get_note_graph_data 錯誤: {e}")
            return {"nodes": [], "edges": []}

def search_notes(telegram_id: int, keyword: str) -> List[Dict]:
    """搜尋筆記"""
    with db_manager.get_session() as session:
        if session is None:
            return []
        
        try:
            notes = session.query(Note).filter(
                Note.telegram_id == telegram_id,
                (Note.title.contains(keyword)) | (Note.content.contains(keyword))
            ).all()
            
            result = []
            for note in notes:
                result.append({
                    'id': note.id,
                    'title': note.title,
                    'content': note.content,
                    'tags': [tag.name for tag in note.tags],
                    'created_at': note.created_at
                })
            
            return result
        
        except Exception as e:
            logger.error(f"search_notes 錯誤: {e}")
            return []