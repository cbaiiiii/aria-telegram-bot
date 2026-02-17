"""
基礎命令處理器
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from database import get_or_create_user, get_user_stats
from services import claude_service
from database.connection import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    user = update.effective_user
    
    # 創建或更新用戶記錄
    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    features = (
        f'🎉 你好 {user.first_name}！\n\n'
        f'我是 Aria，你的 AI 助手！現在有**記憶功能**了！\n\n'
        f'📋 *可用功能：*\n\n'
        f'🤖 *AI 對話*（Claude）\n'
        f'💬 直接發訊息 - 我會記住對話！\n'
        f'/ai <問題> - AI 回答\n'
        f'/clear - 清除對話記憶\n\n'
        f'📝 *筆記系統*\n'
        f'/note <標題> | <內容> - 儲存筆記\n'
        f'/notes - 查看所有筆記\n'
        f'/delnote <編號> - 刪除筆記\n\n'
        f'🛠️ *實用工具*\n'
        f'🌤️ /weather <城市> - 查詢天氣\n'
        f'💱 /currency <金額> <貨幣> - 匯率轉換\n'
        f'🎲 /dice - 擲骰子\n'
        f'🪙 /flip - 擲硬幣\n\n'
        f'📊 /stats - 查看你的使用統計\n'
        f'❓ /help - 詳細說明'
    )
    
    if not claude_service.is_available:
        features += '\n\n⚠️ _Claude AI 未啟用（需要 API Key）_'
    
    await update.message.reply_text(features, parse_mode='Markdown')
    logger.info(f"User {user.id} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    help_text = (
        '📖 *Aria 完整功能說明*\n\n'
        '🤖 *AI 對話（有記憶）*\n'
        '直接發送訊息，我會記住之前的對話！\n'
        '`/ai <問題>` - 單次問答\n'
        '`/clear` - 清除對話記憶\n\n'
        '📝 *筆記系統*（支援知識圖譜）\n'
        '`/note 標題 | 內容` - 儲存筆記\n'
        '• 使用 `#標籤` 來分類\n'
        '• 使用 `[[筆記標題]]` 來連結\n'
        '`/notes` - 查看所有筆記\n'
        '`/graph` - 查看知識圖譜 🌟\n'
        '`/search <關鍵字>` - 搜尋筆記\n'
        '`/delnote <編號>` - 刪除筆記\n\n'
        '🌤️ *天氣查詢*\n'
        '`/weather 台北` - 查詢天氣\n'
        '或直接問：「台北天氣如何？」\n\n'
        '💱 *匯率轉換*\n'
        '`/currency 100 USD` - 轉換匯率\n'
        '或直接問：「100美金多少台幣？」\n\n'
        '🎲 *娛樂*\n'
        '`/dice` - 擲骰子\n'
        '`/flip` - 擲硬幣\n\n'
        '📊 *統計*\n'
        '`/stats` - 查看你的使用統計\n\n'
        '💡 *提示*：我現在有記憶和工具了！\n'
        '試著跟我多聊幾句，或創建筆記來建立你的知識圖譜 🧠'
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
    
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /status 命令"""
    claude_status = '✅ 已啟用' if claude_service.is_available else '❌ 未設定'
    db_status = '✅ 已連線' if db_manager.is_connected else '❌ 未連線'
    
    await update.message.reply_text(
        '✅ *Bot 狀態*\n\n'
        f'🤖 運行模式：Polling\n'
        f'🌐 平台：Railway\n'
        f'📡 狀態：正常運行中\n'
        f'🧠 Claude AI：{claude_status}\n'
        f'💾 資料庫：{db_status}\n'
        f'⚡ 功能：AI對話(記憶)、筆記、天氣、匯率\n'
        f'🔋 響應速度：良好',
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /stats 命令"""
    user = update.effective_user
    
    # 更新用戶記錄
    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    stats = get_user_stats(user.id)
    
    if stats:
        # 計算使用天數
        days_used = (datetime.utcnow() - stats['created_at']).days
        if days_used == 0:
            days_used = "今天剛開始"
        else:
            days_used = f"{days_used} 天"
        
        stats_text = (
            f'📊 *{user.first_name} 的使用統計*\n\n'
            f'📅 使用時間：{days_used}\n'
            f'💬 總訊息數：{stats["message_count"]}\n'
            f'🤖 AI 對話次數：{stats["ai_usage_count"]}\n'
            f'📝 筆記數量：{stats["note_count"]}\n'
            f'🗣️ 對話記錄：{stats["conversation_count"]} 則\n\n'
            f'⏰ 最後活動：{stats["last_active"].strftime("%Y-%m-%d %H:%M")}\n\n'
            f'_持續使用讓我更了解你！_'
        )
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    else:
        await update.message.reply_text('無法取得統計資料 😢')