"""
Aria Telegram Bot - 主程式
一個具有 AI 對話、筆記、天氣查詢等功能的 Telegram 機器人
"""
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.settings import settings
from database.connection import db_manager
from services import claude_service
from utils.logger import setup_logger

# 匯入所有 handlers
from handlers import (
    start_command,
    help_command,
    status_command,
    stats_command,
    ai_command,
    clear_command,
    note_command,
    notes_command,
    delnote_command,
    graph_command,
    search_command,
    weather_command,
    currency_command,
    handle_message,
    # 新增
    daily_command,
    news_command,
    paper_command,
    learn_command,
)

logger = setup_logger(__name__)

def main():
    """主程式入口"""
    # 驗證配置
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"❌ 配置錯誤: {e}")
        return
    
    # 初始化資料庫
    if db_manager.initialize():
        logger.info("✅ 資料庫已初始化")
    else:
        logger.warning("⚠️ 資料庫未初始化,持久化功能將無法使用")
    
    # 檢查 Claude API
    if claude_service.is_available:
        logger.info("✅ Claude AI 已啟用")
    else:
        logger.warning("⚠️ Claude AI 未啟用")
    
    # 創建 Application
    application = Application.builder().token(settings.BOT_TOKEN).build()
    
    # 註冊基礎命令
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # 註冊 AI 相關命令
    application.add_handler(CommandHandler("ai", ai_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # 註冊筆記命令
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("notes", notes_command))
    application.add_handler(CommandHandler("delnote", delnote_command))
    application.add_handler(CommandHandler("graph", graph_command))
    application.add_handler(CommandHandler("search", search_command))
    
    # 註冊工具命令
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("currency", currency_command))
    
    # 註冊每日摘要相關命令
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("paper", paper_command))
    application.add_handler(CommandHandler("learn", learn_command))
    
    # 註冊一般訊息處理器
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # 啟動 bot
    logger.info("🚀 Aria Bot 啟動中...")
    logger.info("✨ 功能：Claude AI、筆記、天氣、匯率、論文搜尋、主題研究、每日摘要")
    
    application.run_polling(allowed_updates=['message'])

if __name__ == '__main__':
    main()