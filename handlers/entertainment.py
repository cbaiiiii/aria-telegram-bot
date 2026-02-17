"""
娛樂功能處理器
"""
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import increment_message_count

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /dice 命令"""
    user = update.effective_user
    increment_message_count(user.id)
    
    result = random.randint(1, 6)
    dice_emoji = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    
    await update.message.reply_text(
        f'🎲 擲骰子...\n\n'
        f'{dice_emoji[result-1]} 結果：*{result}* 點',
        parse_mode='Markdown'
    )

async def flip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /flip 命令"""
    user = update.effective_user
    increment_message_count(user.id)
    
    result = random.choice(['正面 👑', '反面 🦅'])
    
    await update.message.reply_text(
        f'🪙 擲硬幣...\n\n'
        f'結果：*{result}*',
        parse_mode='Markdown'
    )