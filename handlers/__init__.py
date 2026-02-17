"""
Handlers 模組
"""
from .basic import start_command, help_command, status_command, stats_command
from .ai import ai_command, clear_command, handle_message
from .notes import note_command, notes_command, delnote_command, graph_command, search_command
from .tools import weather_command, currency_command

# 新增
from .daily import daily_command, news_command, paper_command, learn_command

__all__ = [
    'start_command',
    'help_command',
    'status_command',
    'stats_command',
    'ai_command',
    'clear_command',
    'handle_message',
    'note_command',
    'notes_command',
    'delnote_command',
    'graph_command',
    'search_command',
    'weather_command',
    'currency_command',
    # 新增
    'daily_command',
    'news_command',
    'paper_command',
    'learn_command',
]