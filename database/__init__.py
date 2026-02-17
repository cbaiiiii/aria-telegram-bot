"""
資料庫模組
"""
from database.connection import db_manager
from database.operations import (
    get_or_create_user,
    increment_message_count,
    increment_ai_usage,
    get_user_stats,
    save_conversation,
    get_conversation_history,
    clear_conversation_history,
    save_note,
    get_user_notes,
    delete_note,
    save_note_with_metadata,  # 新增
    get_note_graph_data,      # 新增
    search_notes              # 新增
)

__all__ = [
    'db_manager',
    'get_or_create_user',
    'increment_message_count',
    'increment_ai_usage',
    'get_user_stats',
    'save_conversation',
    'get_conversation_history',
    'clear_conversation_history',
    'save_note',
    'get_user_notes',
    'delete_note',
    'save_note_with_metadata',
    'get_note_graph_data',
    'search_notes'
]