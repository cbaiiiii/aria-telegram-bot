"""
每日摘要功能處理器
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import increment_message_count
from services import claude_service
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理 /daily 命令 - 生成每日摘要
    包含:天氣、新聞、AI 論文、語言學習
    """
    user = update.effective_user
    increment_message_count(user.id)
    
    if not claude_service.is_available:
        await update.message.reply_text(
            '❌ Claude AI 未啟用\n\n'
            '請設定 ANTHROPIC_API_KEY 環境變數'
        )
        return
    
    await update.message.reply_text(
        '☀️ *每日摘要生成中...*\n\n'
        '正在收集:\n'
        '🌤️ 天氣資訊\n'
        '📰 今日新聞\n'
        '🤖 AI 論文\n'
        '📚 語言學習\n\n'
        '請稍候...',
        parse_mode='Markdown'
    )
    
    # 讓 Claude 自動調用工具生成每日摘要
    daily_prompt = """
請為我生成今日摘要,包含以下內容:

1. 台中的天氣 (使用 get_weather 工具)
2. 今日重要新聞 3-5 則 (使用 fetch_daily_news 工具,category: technology 和 world)
3. 最新的 AI 相關論文 1 篇 (使用 search_arxiv_papers 工具)
4. 每日英文學習內容 (使用 generate_language_lesson 工具,如果沒有這個工具就跳過)

請分別調用這些工具,然後整理成清晰易讀的每日摘要格式。
"""
    
    try:
        # 呼叫 Claude (會自動使用工具)
        messages = [{"role": "user", "content": daily_prompt}]
        response = claude_service.chat(messages, use_tools=True)
        
        # 處理工具調用
        if response["tool_calls"]:
            from handlers.ai import handle_tool_calls
            await handle_tool_calls(update, response["tool_calls"], user.id)
        
        # 顯示 Claude 的總結
        if response["text"]:
            await update.message.reply_text(
                f'━━━━━━━━━━━━━━━━━\n\n{response["text"]}',
                parse_mode='Markdown'
            )
        
        logger.info(f"Daily summary sent to {user.id}")
    
    except Exception as e:
        logger.error(f"Daily command error: {e}", exc_info=True)
        await update.message.reply_text('😥 每日摘要生成失敗,請稍後再試')


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /news 命令 - 只看新聞"""
    user = update.effective_user
    increment_message_count(user.id)
    
    if not claude_service.is_available:
        await update.message.reply_text('❌ Claude AI 未啟用')
        return
    
    # 讓 Claude 調用新聞工具
    prompt = "請使用 fetch_daily_news 工具取得今日重要新聞 5 則"
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = claude_service.chat(messages, use_tools=True)
        
        if response["tool_calls"]:
            from handlers.ai import handle_tool_calls
            await handle_tool_calls(update, response["tool_calls"], user.id)
        
        if response["text"]:
            await update.message.reply_text(response["text"])
    
    except Exception as e:
        logger.error(f"News command error: {e}")
        await update.message.reply_text('😥 新聞取得失敗')


async def paper_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /paper 命令 - 推薦論文"""
    user = update.effective_user
    increment_message_count(user.id)
    
    if not claude_service.is_available:
        await update.message.reply_text('❌ Claude AI 未啟用')
        return
    
    # 讓 Claude 調用論文搜尋工具
    prompt = "請使用 search_arxiv_papers 工具推薦今日最新的 AI 相關論文 3 篇"
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = claude_service.chat(messages, use_tools=True)
        
        if response["tool_calls"]:
            from handlers.ai import handle_tool_calls
            await handle_tool_calls(update, response["tool_calls"], user.id)
        
        if response["text"]:
            await update.message.reply_text(response["text"])
    
    except Exception as e:
        logger.error(f"Paper command error: {e}")
        await update.message.reply_text('😥 論文取得失敗')


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /learn 命令 - 語言學習"""
    user = update.effective_user
    increment_message_count(user.id)
    
    if not claude_service.is_available:
        await update.message.reply_text('❌ Claude AI 未啟用')
        return
    
    # 讓 Claude 生成語言學習內容
    prompt = """
請生成今日英文學習內容,包含:
1. 一個實用的英文句子或片語
2. 中文翻譯
3. 使用情境說明
4. 例句示範

請用清晰易懂的格式呈現。
"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = claude_service.chat(messages, use_tools=False)
        
        if response["text"]:
            formatted_text = f'📚 *每日英文*\n\n{response["text"]}'
            await update.message.reply_text(formatted_text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Learn command error: {e}")
        await update.message.reply_text('😥 學習內容生成失敗')