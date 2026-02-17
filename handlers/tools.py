"""
工具功能處理器
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import increment_message_count
from services import weather_service, currency_service
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /weather 命令"""
    user = update.effective_user
    increment_message_count(user.id)
    
    if not context.args:
        await update.message.reply_text(
            '❌ 請提供城市名稱\n\n'
            '用法：`/weather 台北`',
            parse_mode='Markdown'
        )
        return
    
    city = ' '.join(context.args)
    await update.message.reply_text(f'🔍 正在查詢 {city} 的天氣...')
    
    weather_data = weather_service.get_weather(city)
    
    if weather_data:
        weather_text = (
            f'🌤️ *{weather_data["city"]} 天氣報告*\n\n'
            f'🌡️ 溫度：{weather_data["temp_c"]}°C（體感 {weather_data["feels_like"]}°C）\n'
            f'☁️ 天氣：{weather_data["weather_desc"]}\n'
            f'💧 濕度：{weather_data["humidity"]}%\n'
            f'💨 風速：{weather_data["wind_speed"]} km/h'
        )
        await update.message.reply_text(weather_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(f'❌ 找不到城市「{city}」')

async def currency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /currency 命令"""
    user = update.effective_user
    increment_message_count(user.id)
    
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
        
        result = currency_service.convert(amount, from_currency)
        
        if result:
            result_text = f'💱 *{result["from_amount"]} {result["from_currency"]} 匯率*\n\n'
            
            for code, data in result['results'].items():
                result_text += f'{data["name"]}：`{data["amount"]:,.2f}`\n'
            
            if result.get('date'):
                result_text += f'\n_更新時間：{result["date"]}_'
            
            await update.message.reply_text(result_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(f'❌ 不支援的貨幣：{from_currency}')
    
    except ValueError:
        await update.message.reply_text('❌ 金額格式錯誤')
    except Exception as e:
        logger.error(f"Currency command error: {e}")
        await update.message.reply_text('😥 匯率查詢失敗')