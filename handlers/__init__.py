"""
命令處理器模組
"""
from handlers.basic import (
    start_command,
    help_command,
    status_command,
    stats_command
)
from handlers.ai import (
    ai_command,
    clear_command,
    handle_message
)
from handlers.notes import (
    note_command,
    notes_command,
    delnote_command,
    graph_command,    # 新增
    search_command    # 新增
)
from handlers.tools import (
    weather_command,
    currency_command
)
from handlers.entertainment import (
    dice_command,
    flip_command
)

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
    'dice_command',
    'flip_command'
]