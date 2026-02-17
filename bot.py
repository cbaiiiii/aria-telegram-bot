import os
import logging
import requests
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
    
    features = (
        f'🎉 你好 {user.first_name}！\n\n'
        f'我是 Aria，你的 AI 助手！\n\n'
        f'📋 *可用功能：*\n\n'
        f'🤖 *AI 對話*（Claude）\n'
        f'💬 直接發訊息給我，我會用 AI 回答\n'
        f'或使用 /ai <問題>\n\n'
        f'🛠️ *實用工具*\n'
        f'🌤️ /weather <城市> - 查詢天氣\n'
        f'💱 /currency <金額> <貨幣> - 匯率轉換\n'
        f'🎲 /dice - 擲骰子\n'
        f'🪙 /flip - 擲硬幣\n\n'
        f'❓ /help - 查看詳細說明\n'
        f'📊 /status - Bot 狀態'
    )
    
    if not anthropic_client:
        features += '\n\n⚠️ _Claude AI 未啟用（需要 API Key）_'
    
    await update.message.reply_text(features, parse_mode='Markdown')
    logger.info(f"User {user.id} started the bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        '📖 *Aria 使用說明*\n\n'
        '🤖 *AI 對話（Claude）*\n'
        '直接發送訊息，我會用 Claude AI 回答\n'
        '例如：「幫我寫一首詩」\n'
        '或使用：`/ai 什麼是量子力學？`\n\n'
        '🌤️ *天氣查詢*\n'
        '用法：`/weather 台北`\n\n'
        '💱 *匯率轉換*\n'
        '用法：`/currency 100 USD`\n'
        '支援：USD, EUR, GBP, JPY, TWD, CNY, KRW\n\n'
        '🎲 *娛樂功能*\n'
        '`/dice` - 擲骰子（1-6）\n'
        '`/flip` - 擲硬幣\n\n'
        '💡 *提示*：試著問我任何問題！'
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    claude_status = '✅ 已啟用' if anthropic_client else '❌ 未設定'
    
    await update.message.reply_text(
        '✅ *Bot 狀態*\n\n'
        f'🤖 運行模式：Polling\n'
        f'🌐 平台：Railway\n'
        f'📡 狀態：正常運行中\n'
        f'🧠 Claude AI：{claude_status}\n'
        f'⚡ 功能：AI對話、天氣、匯率、娛樂\n'
        f'🔋 響應速度：良好',
        parse_mode='Markdown'
    )

# ==================== Claude AI 功能 ====================

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """使用 Claude AI 回答問題"""
    if not anthropic_client:
        await update.message.reply_text(
            '❌ Claude AI 未啟用\n\n'
            '請設定 ANTHROPIC_API_KEY 環境變數\n'
            '取得 API Key：https://console.anthropic.com'
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            '❓ 請提供問題\n\n'
            '用法：`/ai 你的問題`\n'
            '例如：`/ai 什麼是機器學習？`',
            parse_mode='Markdown'
        )
        return
    
    question = ' '.join(context.args)
    await ask_claude(update, question)

async def ask_claude(update: Update, question: str):
    """呼叫 Claude API"""
    user = update.effective_user
    
    # 顯示正在思考
    thinking_msg = await update.message.reply_text('🤔 Claude 正在思考...')
    
    try:
        logger.info(f"Claude query from {user.id}: {question}")
        
        # 呼叫 Claude API
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",  # 使用最新的 Claude 模型
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )
        
        # 取得回應
        response = message.content[0].text
        
        # 刪除「思考中」訊息
        await thinking_msg.delete()
        
        # 如果回應太長，分段發送
        if len(response) > 4000:
            # Telegram 訊息限制 4096 字元
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(
                        f'🤖 *Claude 回答：*\n\n{chunk}',
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(
                f'🤖 *Claude 回答：*\n\n{response}',
                parse_mode='Markdown'
            )
        
        logger.info(f"Claude response sent to {user.id}")
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        await thinking_msg.delete()
        await update.message.reply_text(
            '😥 抱歉，Claude 回答時發生錯誤\n\n'
            f'錯誤訊息：{str(e)[:100]}'
        )

# ==================== 天氣功能 ====================

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查詢天氣"""
    if not context.args:
        await update.message.reply_text(
            '❌ 請提供城市名稱\n\n'
            '用法：`/weather 台北` 或 `/weather Tokyo`',
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
                f'💨 風速：{wind_speed} km/h\n\n'
                f'_更新時間：現在_'
            )
            
            await update.message.reply_text(weather_text, parse_mode='Markdown')
            logger.info(f"Weather query for {city} successful")
        else:
            await update.message.reply_text(
                f'❌ 找不到城市「{city}」\n\n'
                f'請檢查拼寫或試試英文名稱'
            )
    
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        await update.message.reply_text(
            '😥 天氣查詢失敗，請稍後再試\n'
            '可能原因：網絡問題或城市名稱錯誤'
        )

# ==================== 匯率功能 ====================

async def currency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """匯率轉換"""
    if len(context.args) < 2:
        await update.message.reply_text(
            '❌ 請提供金額和貨幣\n\n'
            '用法：\n'
            '`/currency 100 USD` - 100美金轉其他貨幣\n'
            '`/currency 3000 TWD` - 3000台幣轉其他貨幣\n\n'
            '支援貨幣：USD, EUR, GBP, JPY, TWD, CNY, KRW',
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
            
            result_text = f'💱 *{amount} {from_currency} 匯率轉換*\n\n'
            
            for code, name in currencies.items():
                if code != from_currency and code in rates:
                    converted = amount * rates[code]
                    result_text += f'{name}（{code}）：`{converted:,.2f}`\n'
            
            result_text += f'\n_更新時間：{data["date"]}_'
            
            await update.message.reply_text(result_text, parse_mode='Markdown')
            logger.info(f"Currency conversion: {amount} {from_currency}")
        else:
            await update.message.reply_text(
                f'❌ 不支援的貨幣：{from_currency}\n\n'
                f'支援的貨幣：USD, EUR, GBP, JPY, TWD, CNY, KRW'
            )
    
    except ValueError:
        await update.message.reply_text('❌ 金額格式錯誤，請輸入數字')
    except Exception as e:
        logger.error(f"Currency API error: {e}")
        await update.message.reply_text(
            '😥 匯率查詢失敗，請稍後再試'
        )

# ==================== 娛樂功能 ====================

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """擲骰子"""
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
    import random
    result = random.choice(['正面 👑', '反面 🦅'])
    
    await update.message.reply_text(
        f'🪙 擲硬幣...\n\n'
        f'結果：*{result}*',
        parse_mode='Markdown'
    )

# ==================== 一般訊息處理 ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息 - 使用 Claude AI 回答"""
    user_message = update.message.text
    user = update.effective_user
    
    logger.info(f"Message from {user.id}: {user_message}")
    
    # 如果 Claude 可用，用 AI 回答
    if anthropic_client:
        await ask_claude(update, user_message)
    else:
        # Claude 未啟用時的預設回應
        await update.message.reply_text(
            f'📨 你說："{user_message}"\n\n'
            f'我收到了！\n\n'
            f'💡 提示：設定 ANTHROPIC_API_KEY 後，我就能用 Claude AI 回答你的問題了！\n\n'
            f'使用 /help 查看其他功能'
        )

# ==================== 主程式 ====================

def main():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN 環境變數未設置！")
        return
    
    # 檢查 Claude API Key
    if ANTHROPIC_API_KEY:
        logger.info("✅ Claude API Key 已設置")
    else:
        logger.warning("⚠️ ANTHROPIC_API_KEY 未設置，AI 功能將無法使用")
    
    application = Application.builder().token(TOKEN).build()
    
    # 添加命令處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("ai", ai_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("currency", currency_command))
    application.add_handler(CommandHandler("dice", dice_command))
    application.add_handler(CommandHandler("flip", flip_command))
    
    # 一般訊息處理（使用 Claude）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🚀 Aria Bot 啟動中...")
    logger.info("✨ 功能：Claude AI、天氣、匯率、娛樂")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
