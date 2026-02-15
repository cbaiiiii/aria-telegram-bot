import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f'🎉 你好 {user.first_name}！\n\n'
        f'我是 Aria！\n\n'
        f'可用命令：\n'
        f'/start - 開始對話\n'
        f'/help - 查看幫助\n'
        f'/status - 查看狀態'
    )
    logger.info(f"User {user.id} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '👋 *Aria 使用說明*\n\n'
        '🔹 /start - 開始使用\n'
        '🔹 /help - 顯示此幫助訊息\n'
        '🔹 /status - 查看 bot 運行狀態\n\n'
        '💬 直接發送訊息給我，我會回覆你！',
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '✅ *Bot 狀態*\n\n'
        f'🤖 運行模式：Polling\n'
        f'🌐 平台：Railway\n'
        f'📡 狀態：正常運行中\n'
        f'⚡ 響應時間：良好',
        parse_mode='Markdown'
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.effective_user
    logger.info(f"Received message from {user.id}: {user_message}")
    await update.message.reply_text(f'📨 你說："{user_message}"\n\n我收到了！')

def main():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN 環境變數未設置！")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("🚀 Bot 啟動中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
