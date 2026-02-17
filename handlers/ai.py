"""
AI 相關功能處理器（支援 Tool Use）
"""
from telegram import Update
from telegram.ext import ContextTypes
from typing import List, Dict

from database import (
    get_or_create_user,
    increment_ai_usage,
    increment_message_count,
    save_conversation,
    get_conversation_history,
    clear_conversation_history,
    save_note
)
from services import claude_service, weather_service, currency_service
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /ai 命令"""
    if not claude_service.is_available:
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
    """處理 /clear 命令"""
    user = update.effective_user
    success = clear_conversation_history(user.id)
    
    if success:
        await update.message.reply_text(
            '🧹 *對話記憶已清除*\n\n'
            '我們重新開始吧！',
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text('清除失敗 😢')

async def ask_claude(update: Update, question: str, save_history: bool = True):
    """
    呼叫 Claude API（帶對話記憶和工具調用）
    """
    user = update.effective_user
    
    # 更新用戶記錄
    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    # 增加 AI 使用計數
    increment_ai_usage(user.id)
    
    # 顯示正在思考
    thinking_msg = await update.message.reply_text('🤔 Claude 正在思考...')
    
    try:
        logger.info(f"Claude query from {user.id}: {question}")
        
        # 取得對話歷史
        history = get_conversation_history(
            user.id, 
            limit=settings.CONVERSATION_HISTORY_LIMIT
        )
        
        # 構建訊息列表
        messages = []
        
        # 加入歷史對話
        for conv in history:
            messages.append({
                "role": conv['role'],
                "content": conv['content']
            })
        
        # 加入當前問題
        messages.append({
            "role": "user",
            "content": question
        })
        
        # 呼叫 Claude API（啟用工具）
        response = claude_service.chat(messages, use_tools=True)
        
        if response["text"] is None and not response["tool_calls"]:
            await thinking_msg.delete()
            await update.message.reply_text('😥 抱歉，Claude 回答時發生錯誤')
            return
        
        # 刪除思考訊息
        await thinking_msg.delete()
        
        # 處理工具調用
        if response["tool_calls"]:
            tool_results = await handle_tool_calls(update, response["tool_calls"], user.id)
            
            # 如果 Claude 還有文字說明，也顯示
            if response["text"]:
                await update.message.reply_text(response["text"])
            
            # 儲存對話（包含工具使用）
            if save_history:
                save_conversation(user.id, "user", question)
                # 簡化儲存：只儲存 Claude 的文字回應
                if response["text"]:
                    save_conversation(user.id, "assistant", response["text"])
                else:
                    # 如果只有工具調用，儲存工具結果摘要
                    summary = f"我幫你查詢了：{', '.join([tc['name'] for tc in response['tool_calls']])}"
                    save_conversation(user.id, "assistant", summary)
        
        # 只有文字回應
        elif response["text"]:
            # 儲存對話
            if save_history:
                save_conversation(user.id, "user", question)
                save_conversation(user.id, "assistant", response["text"])
            
            # 處理長回應
            if len(response["text"]) > 4000:
                chunks = [response["text"][i:i+4000] for i in range(0, len(response["text"]), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(response["text"])
        
        logger.info(f"Claude response sent to {user.id}")
        
    except Exception as e:
        logger.error(f"ask_claude error: {e}", exc_info=True)
        try:
            await thinking_msg.delete()
        except:
            pass
        await update.message.reply_text(f'😥 抱歉，發生錯誤\n\n錯誤：{str(e)[:100]}')


async def handle_tool_calls(update: Update, tool_calls: List[Dict], telegram_id: int) -> List[str]:
    """
    處理 Claude 的工具調用
    
    Returns:
        工具執行結果列表
    """
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_input = tool_call["input"]
        
        logger.info(f"Tool call: {tool_name} with input: {tool_input}")
        
        # 天氣查詢
        if tool_name == "get_weather":
            city = tool_input.get("city", "")
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
                results.append(f"成功查詢 {city} 天氣")
            else:
                await update.message.reply_text(f'❌ 找不到城市「{city}」，請檢查拼寫')
                results.append(f"找不到城市 {city}")
        
        # 匯率轉換
        elif tool_name == "convert_currency":
            amount = tool_input.get("amount", 0)
            from_currency = tool_input.get("from_currency", "").upper()
            
            await update.message.reply_text(f'🔄 正在轉換 {amount} {from_currency}...')
            
            result = currency_service.convert(amount, from_currency)
            
            if result:
                result_text = f'💱 *{result["from_amount"]} {result["from_currency"]} 匯率轉換*\n\n'
                
                for code, data in result['results'].items():
                    result_text += f'{data["name"]}：`{data["amount"]:,.2f}`\n'
                
                if result.get('date'):
                    result_text += f'\n_更新時間：{result["date"]}_'
                
                await update.message.reply_text(result_text, parse_mode='Markdown')
                results.append(f"成功轉換 {amount} {from_currency}")
            else:
                await update.message.reply_text(f'❌ 不支援的貨幣：{from_currency}\n\n支援：USD, EUR, GBP, JPY, TWD, CNY, KRW')
                results.append(f"不支援的貨幣 {from_currency}")
        
        # 儲存筆記
        elif tool_name == "save_note":
            title = tool_input.get("title", "")
            content = tool_input.get("content", "")
            
            # 使用支援標籤和連結的版本
            from database import save_note_with_metadata
            note_data = save_note_with_metadata(telegram_id, title, content)
            
            if note_data:
                response = f'✅ *筆記已儲存*\n\n📌 標題：{title}\n'
                
                if note_data.get('tags'):
                    response += f'🏷️ 標籤：{", ".join(["#" + tag for tag in note_data["tags"]])}\n'
                
                if note_data.get('links'):
                    response += f'🔗 連結：{", ".join(note_data["links"])}\n'
                
                response += f'\n使用 /graph 查看知識圖譜'
                
                await update.message.reply_text(response, parse_mode='Markdown')
                results.append(f"成功儲存筆記: {title}")
            else:
                await update.message.reply_text('😢 筆記儲存失敗')
                results.append("筆記儲存失敗")

        # 新聞查詢
        elif tool_name == "fetch_daily_news":
            from services.news_service import news_service
            
            category = tool_input.get("category", "all")
            max_items = tool_input.get("max_items", 5)
            
            await update.message.reply_text(f'📰 正在取得新聞...')
            
            news_list = news_service.fetch_news(category, max_items)
            
            if news_list:
                news_text = '📰 *今日新聞*\n\n'
                for i, news in enumerate(news_list, 1):
                    news_text += f'*{i}. {news["title"]}*\n'
                    if news.get('published'):
                        news_text += f'📅 {news.get("published", "")[:16]} | 📰 {news.get("source", "")}\n'
                    if news.get('summary'):
                        news_text += f'{news["summary"]}\n'
                    if news.get('link'):
                        news_text += f'🔗 [閱讀全文]({news["link"]})\n'
                    news_text += '\n'
                
                await update.message.reply_text(
                    news_text, 
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                results.append(f"成功取得 {len(news_list)} 則新聞")
            else:
                await update.message.reply_text('❌ 新聞取得失敗')
                results.append("新聞取得失敗")

        # AI 論文搜尋
        elif tool_name == "search_arxiv_papers":
            from services.arxiv_service import arxiv_service
            
            query = tool_input.get("query", "")
            category = tool_input.get("category", "all")
            max_results = tool_input.get("max_results", 3)
            sort_by = tool_input.get("sort_by", "relevance")
            
            # 顯示搜尋訊息
            if query:
                await update.message.reply_text(f'🔍 正在搜尋「{query}」相關論文...')
            else:
                await update.message.reply_text(f'🔍 正在取得最新 AI 論文...')
            
            # 呼叫 arXiv 搜尋
            papers = arxiv_service.search_papers(query, category, max_results, sort_by)
            
            if papers:
                # 格式化輸出
                paper_text = f'🤖 *找到 {len(papers)} 篇論文*\n\n'
                
                for i, paper in enumerate(papers, 1):
                    paper_text += f'*{i}. {paper["title"]}*\n'
                    paper_text += f'👥 {", ".join(paper["authors"])}\n'
                    paper_text += f'📅 {paper["published"]} | 🆔 {paper["id"]}\n'
                    paper_text += f'📝 {paper["summary"]}\n'
                    paper_text += f'🔗 [論文]({paper["web_url"]}) | [PDF]({paper["pdf_url"]})\n\n'
                
                # Telegram 訊息長度限制 4096 字
                if len(paper_text) > 4000:
                    # 分段發送
                    chunks = []
                    current_chunk = f'🤖 *找到 {len(papers)} 篇論文*\n\n'
                    
                    for i, paper in enumerate(papers, 1):
                        paper_block = (
                            f'*{i}. {paper["title"]}*\n'
                            f'👥 {", ".join(paper["authors"])}\n'
                            f'📅 {paper["published"]} | 🆔 {paper["id"]}\n'
                            f'📝 {paper["summary"]}\n'
                            f'🔗 [論文]({paper["web_url"]}) | [PDF]({paper["pdf_url"]})\n\n'
                        )
                        
                        if len(current_chunk) + len(paper_block) > 4000:
                            chunks.append(current_chunk)
                            current_chunk = paper_block
                        else:
                            current_chunk += paper_block
                    
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # 發送所有分段
                    for chunk in chunks:
                        await update.message.reply_text(
                            chunk, 
                            parse_mode='Markdown', 
                            disable_web_page_preview=True
                        )
                else:
                    await update.message.reply_text(
                        paper_text, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=True
                    )
                
                results.append(f"找到 {len(papers)} 篇論文")
            else:
                if query:
                    await update.message.reply_text(f'❌ 找不到「{query}」相關論文\n\n試試其他關鍵字或類別')
                else:
                    await update.message.reply_text('❌ 論文取得失敗,請稍後再試')
                results.append("未找到論文")

        # 語言學習
        elif tool_name == "generate_language_lesson":
            language = tool_input.get("language", "english")
            level = tool_input.get("level", "intermediate")
            topic = tool_input.get("topic", "random")
            
            # 語言學習內容由 Claude 直接生成
            # 不需要外部 API,Claude 會根據參數生成內容
            lesson_prompt = f"請生成一個 {language} 的 {level} 難度學習內容,主題是 {topic}。包含實用句子、翻譯、發音提示、例句"
            
            # 這裡 Claude 會在回應中直接包含學習內容
            # 所以我們只需要告訴使用者正在生成
            await update.message.reply_text(f'📚 正在生成 {language} 學習內容...')
            results.append(f"生成 {language} 學習內容")

        # 主題研究
        elif tool_name == "research_topic":
            from services.research_service import research_service
            
            topic = tool_input.get("topic", "")
            focus = tool_input.get("focus", "overview")
            depth = tool_input.get("depth", "detailed")
            
            await update.message.reply_text(f'🔍 正在深度研究「{topic}」...\n\n這需要幾秒鐘...')
            
            # 收集資訊
            research_data = research_service.research_topic(topic, focus, depth)
            
            # 格式化收集到的資料
            data_summary = f'已收集到以下資訊:\n\n'
            
            # 論文
            if research_data['papers']:
                data_summary += f'📚 找到 {len(research_data["papers"])} 篇論文:\n'
                for p in research_data['papers']:
                    data_summary += f'- {p["title"]} ({p["published"]})\n'
                    data_summary += f'  摘要: {p["summary"][:150]}...\n\n'
            
            # 網路資源
            if research_data['web_articles']:
                data_summary += f'🌐 找到 {len(research_data["web_articles"])} 個網路資源:\n'
                for a in research_data['web_articles']:
                    if a.get('snippet'):
                        data_summary += f'- {a.get("title", "")[:80]}\n'
                        data_summary += f'  {a["snippet"][:100]}...\n\n'
            
            # GitHub
            if research_data['github']:
                gh = research_data['github']
                data_summary += f'💻 GitHub 專案:\n'
                data_summary += f'- {gh["name"]} (⭐ {gh["stars"]:,})\n'
                data_summary += f'  {gh["description"]}\n\n'
            
            # ⭐ 關鍵:自動觸發第二輪分析
            await update.message.reply_text('💡 正在綜合分析...')
            
            # 建構分析提示
            analysis_prompt = f"""
基於以下收集到的資訊,請生成一份關於「{topic}」的綜合報告。

{data_summary}

請包含:
1. 📋 概述 (這是什麼)
2. 🎯 核心功能/特點
3. 💡 主要應用場景
4. ✅ 優勢
5. ⚠️ 限制或注意事項

請用繁體中文,以清晰易懂的方式說明。
"""
            
            # 呼叫 Claude 生成分析
            analysis_response = claude_service.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                use_tools=False  # 這次不需要工具
            )
            
            if analysis_response["text"]:
                # 先發送資源連結
                links_text = f'📊 *{topic} 研究報告*\n\n'
                
                if research_data['papers']:
                    links_text += '📚 *相關論文*\n'
                    for i, p in enumerate(research_data['papers'], 1):
                        links_text += f'{i}. [{p["title"][:60]}...]({p["web_url"]})\n'
                    links_text += '\n'
                
                if research_data['github']:
                    links_text += f'💻 *GitHub*: [{research_data["github"]["name"]}]({research_data["github"]["url"]})\n\n'
                
                if research_data['web_articles']:
                    links_text += '🌐 *網路資源*\n'
                    for i, a in enumerate(research_data['web_articles'], 1):
                        if a.get('url'):
                            links_text += f'{i}. [{a.get("title", "資源")[:50]}]({a["url"]})\n'
                    links_text += '\n'
                
                links_text += '━━━━━━━━━━━━━━━━━\n\n'
                
                await update.message.reply_text(
                    links_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                
                # 再發送分析報告
                await update.message.reply_text(analysis_response["text"])
                
                results.append(f"完成 {topic} 深度研究")
            else:
                await update.message.reply_text('❌ 分析失敗')
                results.append("分析失敗")
    
    return results


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理一般訊息 - 使用 Claude AI 回答（帶記憶和工具）
    """
    user_message = update.message.text
    user = update.effective_user
    
    # 更新用戶記錄和計數
    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    increment_message_count(user.id)
    
    logger.info(f"Message from {user.id}: {user_message}")
    
    # 如果 Claude 可用，用 AI 回答（帶記憶和工具）
    if claude_service.is_available:
        await ask_claude(update, user_message, save_history=True)
    else:
        # Claude 未啟用
        await update.message.reply_text(
            f'📨 你說："{user_message}"\n\n'
            f'我收到了！\n\n'
            f'💡 提示：設定 ANTHROPIC_API_KEY 後，我就能用 Claude AI 回答你的問題了！\n\n'
            f'使用 /help 查看其他功能'
        )