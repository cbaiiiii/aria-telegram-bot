import os
import logging
import requests
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# 匯入資料庫模組
import database as db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('BOT_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

# 初始化 Anthropic client
anthropic_client = None
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ==================== 基礎命令 ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # 創建或更新用戶記錄
    db_user = db.get_or_create_user(
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
    
    if not anthropic_client:
        features += '\n\n⚠️ _Claude AI 未啟用（需要 API Key）_'
    
    await update.message.reply_text(features, parse_mode='Markdown')
    logger.info(f"User {user.id} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        '📖 *Aria 完整功能說明*\n\n'
        '🤖 *AI 對話（有記憶）*\n'
        '直接發送訊息，我會記住之前的對話！\n'
        '`/ai <問題>` - 單次問答\n'
        '`/clear` - 清除對話記憶\n\n'
        '📝 *筆記系統*\n'
        '`/note 標題 | 內容` - 儲存筆記\n'
        '例如：`/note 待辦 | 買牛奶、寫報告`\n'
        '`/notes` - 查看所有筆記\n'
        '`/delnote 1` - 刪除編號 1 的筆記\n\n'
        '🌤️ *天氣查詢*\n'
        '`/weather 台北` - 查詢天氣\n\n'
        '💱 *匯率轉換*\n'
        '`/currency 100 USD` - 轉換匯率\n\n'
        '🎲 *娛樂*\n'
        '`/dice` - 擲骰子\n'
        '`/flip` - 擲硬幣\n\n'
        '📊 *統計*\n'
        '`/stats` - 查看你的使用統計\n\n'
        '💡 *提示*：我現在有記憶了！試著跟我多聊幾句 😊'
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """顯示用戶統計"""
    user = update.effective_user
    
    # 更新用戶記錄
    db.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    stats = db.get_user_stats(user.id)
    
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

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    claude_status = '✅ 已啟用' if anthropic_client else '❌ 未設定'
    db_status = '✅ 已連線' if db.engine else '❌ 未連線'
    
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

# ==================== Claude AI 功能（帶記憶）====================

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """使用 Claude AI 回答問題"""
    if not anthropic_client:
        await update.message.reply_text(
            '❌ Claude AI 未啟用\n\n'
            '請設定 ANTHROPIC_API_KEY 環境變數'
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            '❓ 請提供問題\n\n'
            '用法：`/ai 你的問題`',
            parse_mode='Markdown'
        )
        return
    
    question = ' '.join(context.args)
    await ask_claude(update, question, save_history=True)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清除對話歷史"""
    user = update.effective_user
    success = db.clear_conversation_history(user.id)
    
    if success:
        await update.message.reply_text(
            '🧹 *對話記憶已清除*\n\n'
            '我們重新開始吧！',
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text('清除失敗 😢')

async def ask_claude(update: Update, question: str, save_history: bool = True):
    """呼叫 Claude API（帶對話記憶）"""
    user = update.effective_user
    
    # 更新用戶記錄
    db.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    # 增加 AI 使用計數
    db.increment_ai_usage(user.id)
    
    # 顯示正在思考
    thinking_msg = await update.message.reply_text('🤔 Claude 正在思考...')
    
    try:
        logger.info(f"Claude query from {user.id}: {question}")
        
        # 取得對話歷史
        history = db.get_conversation_history(user.id, limit=10)
        
        # 構建訊息列表
        messages = []
        
        # 加入歷史對話
        for conv in history:
            messages.append({
                "role": conv.role,
                "content": conv.content
            })
        
        # 加入當前問題
        messages.append({
            "role": "user",
            "content": question
        })
        
        # 呼叫 Claude API
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system="你是 Aria，一個友善且樂於助人的 AI 助手。你會記住之前的對話內容，並提供連貫、有幫助的回答。",
            messages=messages
        )
        
        # 取得回應
        response = message.content[0].text
        
        # 儲存對話（如果啟用）
        if save_history:
            db.save_conversation(user.id, "user", question)
            db.save_conversation(user.id, "assistant", response)
        
        # 刪除「思考中」訊息
        await thinking_msg.delete()
        
        # 處理長回應
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(
                        f'🤖 *Claude：*\n\n{chunk}',
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(response)
        
        logger.info(f"Claude response sent to {user.id}")
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        await thinking_msg.delete()
        await update.message.reply_text(
            '😥 抱歉，發生錯誤\n\n'
            f'錯誤：{str(e)[:100]}'
        )

# ==================== 筆記功能 ====================

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """儲存筆記"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            '📝 *筆記功能*\n\n'
            '用法：`/note 標題 | 內容`\n\n'
            '例如：\n'
            '`/note 待辦事項 | 買牛奶、寫報告`\n'
            '`/note Python 筆記 | 記得用 async/await`',
            parse_mode='Markdown'
        )
        return
    
    # 解析標題和內容
    text = ' '.join(context.args)
    
    if '|' in text:
        parts = text.split('|', 1)
        title = parts[0].strip()
        content = parts[1].strip()
    else:
        title = f"筆記 {datetime.now().strftime('%m/%d %H:%M')}"
        content = text
    
    # 儲存筆記
    note = db.save_note(user.id, title, content)
    
    if note:
        await update.message.reply_text(
            f'✅ *筆記已儲存*\n\n'
            f'📌 標題：{title}\n'
            f'📄 內容：{content[:50]}{"..." if len(content) > 50 else ""}\n\n'
            f'使用 /notes 查看所有筆記',
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text('儲存失敗 😢')

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看所有筆記"""
    user = update.effective_user
    notes = db.get_user_notes(user.id)
    
    if not notes:
        await update.message.reply_text(
            '📝 *你還沒有筆記*\n\n'
            '使用 `/note 標題 | 內容` 創建筆記',
            parse_mode='Markdown'
        )
        return
    
    # 構建筆記列表
    notes_text = f'📚 *你的筆記（共 {len(notes)} 則）*\n\n'
    
    for i, note in enumerate(notes, 1):
        created = note.created_at.strftime('%m/%d %H:%M')
        content_preview = note.content[:30] + '...' if len(note.content) > 30 else note.content
        notes_text += (
            f'`{i}.` **{note.title}**\n'
            f'   {content_preview}\n'
            f'   _({created})_\n\n'
        )
    
    notes_text += '使用 `/delnote <編號>` 刪除筆記'
    
    await update.message.reply_text(notes_text, parse_mode='Markdown')

async def delnote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """刪除筆記"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            '❌ 請提供筆記編號\n\n'
            '用法：`/delnote 1`\n'
            '先用 /notes 查看編號',
            parse_mode='Markdown'
        )
        return
    
    try:
        # 取得編號
        note_num = int(context.args[0])
        
        # 取得用戶的筆記
        notes = db.get_user_notes(user.id)
        
        if note_num < 1 or note_num > len(notes):
            await update.message.reply_text(f'❌ 編號 {note_num} 不存在')
            return
        
        # 取得要刪除的筆記
        note_to_delete = notes[note_num - 1]
        
        # 刪除筆記
        success = db.delete_note(user.id, note_to_delete.id)
        
        if success:
            await update.message.reply_text(
                f'🗑️ *筆記已刪除*\n\n'
                f'標題：{note_to_delete.title}',
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text('刪除失敗 😢')
            
    except ValueError:
        await update.message.reply_text('❌ 請提供有效的數字')

# ==================== 天氣功能（保持不變）====================

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查詢天氣"""
    user = update.effective_user
    db.increment_message_count(user.id)
    
    if not context.args:
        await update.message.reply_text(
            '❌ 請提供城市名稱\n\n'
            '用法：`/weather 台北`',
            parse_mode='Markdown'
        )
        return
    
    city = ' '.join(context.args)
    await update.message.reply_text(f'🔍 正在查詢 {city} 的天氣...')
    
    try:
        url = f'https://wttr.in/{city}?format=j1'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            temp_c = current['temp_C']
            feels_like = current['FeelsLikeC']
            humidity = current['humidity']
            weather_desc = current['weatherDesc'][0]['value']
            wind_speed = current['windspeedKmph']
            
            weather_text = (
                f'🌤️ *{city} 天氣報告*\n\n'
                f'🌡️ 溫度：{temp_c}°C（體感 {feels_like}°C）\n'
                f'☁️ 天氣：{weather_desc}\n'
                f'💧 濕度：{humidity}%\n'
                f'💨 風速：{wind_speed} km/h'
            )
            
            await update.message.reply_text(weather_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(f'❌ 找不到城市「{city}」')
    
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        await update.message.reply_text('😥 天氣查詢失敗')

# ==================== 匯率功能（保持不變）====================

async def currency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """匯率轉換"""
    user = update.effective_user
    db.increment_message_count(user.id)
    
    if len(context.args) < 2:
        await update.message.reply_text(
            '❌ 請提供金額和貨幣\n\n'
            '用法：`/currency 100 USD`',
            parse_mode='Markdown'
        )
        return
    
    try:
        amount = float(context.args[0])
        from_currency = context.args[1].upper()
        
        await update.message.reply_text(f'🔄 正在轉換 {amount} {from_currency}...')
        
        url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = data['rates']
            
            currencies = {
                'TWD': '台幣',
                'USD': '美金',
                'EUR': '歐元',
                'GBP': '英鎊',
                'JPY': '日圓',
                'CNY': '人民幣',
                'KRW': '韓元'
            }
            
            result_text = f'💱 *{amount} {from_currency} 匯率*\n\n'
            
            for code, name in currencies.items():
                if code != from_currency and code in rates:
                    converted = amount * rates[code]
                    result_text += f'{name}：`{converted:,.2f}`\n'
            
            await update.message.reply_text(result_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(f'❌ 不支援的貨幣：{from_currency}')
    
    except ValueError:
        await update.message.reply_text('❌ 金額格式錯誤')
    except Exception as e:
        logger.error(f"Currency API error: {e}")
        await update.message.reply_text('😥 匯率查詢失敗')

# ==================== 娛樂功能（保持不變）====================

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """擲骰子"""
    user = update.effective_user
    db.increment_message_count(user.id)
    
    import random
    result = random.randint(1, 6)
    dice_emoji = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    
    await update.message.reply_text(
        f'🎲 擲骰子...\n\n'
        f'{dice_emoji[result-1]} 結果：*{result}* 點',
        parse_mode='Markdown'
    )

async def flip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """擲硬幣"""
    user = update.effective_user
    db.increment_message_count(user.id)
    
    import random
    result = random.choice(['正面 👑', '反面 🦅'])
    
    await update.message.reply_text(
        f'🪙 擲硬幣...\n\n'
        f'結果：*{result}*',
        parse_mode='Markdown'
    )

# ==================== 一般訊息處理（帶記憶）====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息 - 使用 Claude AI 回答（帶記憶）"""
    user_message = update.message.text
    user = update.effective_user
    
    # 更新用戶記錄和計數
    db.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    db.increment_message_count(user.id)
    
    logger.info(f"Message from {user.id}: {user_message}")
    
    # 如果 Claude 可用，用 AI 回答（帶記憶）
    if anthropic_client:
        await ask_claude(update, user_message, save_history=True)
    else:
        # Claude 未啟用
        await update.message.reply_text(
            f'📨 你說："{user_message}"\n\n'
            f'我收到了！使用 /help 查看功能'
        )

# ==================== 主程式 ====================

def main():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN 環境變數未設置！")
        return
    
    # 初始化資料庫
    db_initialized = db.init_db()
    if db_initialized:
        logger.info("✅ 資料庫已初始化")
    else:
        logger.warning("⚠️ 資料庫未初始化，持久化功能將無法使用")
    
    # 檢查 Claude API Key
    if ANTHROPIC_API_KEY:
        logger.info("✅ Claude API Key 已設置")
    else:
        logger.warning("⚠️ ANTHROPIC_API_KEY 未設置")
    
    application = Application.builder().token(TOKEN).build()
    
    # 添加命令處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("ai", ai_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("notes", notes_command))
    application.add_handler(CommandHandler("delnote", delnote_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("currency", currency_command))
    application.add_handler(CommandHandler("dice", dice_command))
    application.add_handler(CommandHandler("flip", flip_command))
    
    # 一般訊息處理（使用 Claude + 記憶）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🚀 Aria Bot 啟動中...")
    logger.info("✨ 功能：Claude AI(記憶)、筆記、天氣、匯率、統計")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
