"""
筆記功能處理器（支援 Graph View）
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from database import (
    save_note, 
    get_user_notes, 
    delete_note,
    save_note_with_metadata,
    get_note_graph_data,
    search_notes
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /note 命令（支援標籤和連結）"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            '📝 *筆記功能*\n\n'
            '用法：`/note 標題 | 內容`\n\n'
            '✨ *進階功能*：\n'
            '• 使用 `#標籤` 來分類筆記\n'
            '• 使用 `[[筆記標題]]` 來連結其他筆記\n\n'
            '例如：\n'
            '`/note Python 學習 | 今天學了 async/await #程式設計`\n'
            '`/note 專案規劃 | 參考 [[Python 學習]] 的內容`',
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
    
    # 儲存筆記（帶標籤和連結）
    note_data = save_note_with_metadata(user.id, title, content)
    
    if note_data:
        response = f'✅ *筆記已儲存*\n\n📌 標題：{title}\n'
        
        if note_data['tags']:
            response += f'🏷️ 標籤：{", ".join(["#" + tag for tag in note_data["tags"]])}\n'
        
        if note_data['links']:
            response += f'🔗 連結：{", ".join(note_data["links"])}\n'
        
        response += f'\n使用 /notes 查看所有筆記\n使用 /graph 查看知識圖譜'
        
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text('儲存失敗 😢')

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /notes 命令"""
    user = update.effective_user
    notes = get_user_notes(user.id)
    
    if not notes:
        await update.message.reply_text(
            '📝 *你還沒有筆記*\n\n'
            '使用 `/note 標題 | 內容` 創建筆記\n\n'
            '💡 提示：可以用 #標籤 和 [[連結]] 來組織筆記！',
            parse_mode='Markdown'
        )
        return
    
    # 構建筆記列表
    notes_text = f'📚 *你的筆記（共 {len(notes)} 則）*\n\n'
    
    for i, note in enumerate(notes, 1):
        created = note['created_at'].strftime('%m/%d %H:%M')
        content_preview = note['content'][:30] + '...' if len(note['content']) > 30 else note['content']
        notes_text += (
            f'`{i}.` **{note["title"]}**\n'
            f'   {content_preview}\n'
            f'   _({created})_\n\n'
        )
    
    notes_text += '使用 `/delnote <編號>` 刪除筆記\n'
    notes_text += '使用 `/graph` 查看知識圖譜'
    
    await update.message.reply_text(notes_text, parse_mode='Markdown')

async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /graph 命令 - 生成並顯示知識圖譜"""
    user = update.effective_user
    
    # 發送處理中訊息
    processing_msg = await update.message.reply_text('🎨 正在生成知識圖譜...')
    
    try:
        # 取得圖譜資料
        graph_data = get_note_graph_data(user.id)
        
        if not graph_data['nodes']:
            await processing_msg.edit_text(
                '📊 *知識圖譜*\n\n'
                '你還沒有足夠的筆記來生成圖譜\n\n'
                '創建更多筆記，並使用 #標籤 和 [[連結]] 來建立關聯！',
                parse_mode='Markdown'
            )
            return
        
        # 生成統計資訊
        nodes_count = len(graph_data['nodes'])
        links_count = len([e for e in graph_data['edges'] if e['type'] == 'link'])
        tag_connections = len([e for e in graph_data['edges'] if e['type'] == 'tag'])
        
        caption = (
            f'🧠 *你的知識圖譜*\n\n'
            f'📝 筆記數量：{nodes_count}\n'
            f'🔗 直接連結：{links_count}\n'
            f'🏷️ 標籤關聯：{tag_connections}\n\n'
            f'💡 節點大小表示連結數，顏色深淺表示標籤數'
        )
        
        # 生成圖片
        from services import graph_service
        
        if nodes_count < 3:
            # 筆記太少，生成統計圖表
            image_buf = graph_service.generate_simple_stats_image(graph_data)
            caption = (
                f'📊 *筆記統計*\n\n'
                f'目前有 {nodes_count} 則筆記\n\n'
                f'💡 創建更多筆記並使用 [[連結]] 來看到完整的知識圖譜！'
            )
        else:
            # 生成完整圖譜
            image_buf = graph_service.generate_graph_image(graph_data)
        
        if image_buf:
            # 刪除處理中訊息
            await processing_msg.delete()
            
            # 發送圖片
            await update.message.reply_photo(
                photo=image_buf,
                caption=caption,
                parse_mode='Markdown'
            )
            
            logger.info(f"成功發送知識圖譜給用戶 {user.id}")
        else:
            await processing_msg.edit_text('😢 圖譜生成失敗，請稍後再試')
    
    except Exception as e:
        logger.error(f"graph_command 錯誤: {e}", exc_info=True)
        try:
            await processing_msg.edit_text('😢 生成圖譜時發生錯誤')
        except:
            await update.message.reply_text('😢 生成圖譜時發生錯誤')
            
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /search 命令"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            '🔍 *搜尋筆記*\n\n'
            '用法：`/search 關鍵字`',
            parse_mode='Markdown'
        )
        return
    
    keyword = ' '.join(context.args)
    results = search_notes(user.id, keyword)
    
    if not results:
        await update.message.reply_text(f'😔 找不到包含「{keyword}」的筆記')
        return
    
    response = f'🔍 *搜尋結果：「{keyword}」*\n\n'
    response += f'找到 {len(results)} 則筆記：\n\n'
    
    for i, note in enumerate(results[:10], 1):  # 限制顯示 10 則
        content_preview = note['content'][:50] + '...' if len(note['content']) > 50 else note['content']
        response += f'`{i}.` **{note["title"]}**\n'
        response += f'   {content_preview}\n\n'
    
    if len(results) > 10:
        response += f'_還有 {len(results) - 10} 則結果未顯示_'
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def delnote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /delnote 命令"""
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
        note_num = int(context.args[0])
        notes = get_user_notes(user.id)
        
        if note_num < 1 or note_num > len(notes):
            await update.message.reply_text(f'❌ 編號 {note_num} 不存在')
            return
        
        note_to_delete = notes[note_num - 1]
        success = delete_note(user.id, note_to_delete['id'])
        
        if success:
            await update.message.reply_text(
                f'🗑️ *筆記已刪除*\n\n'
                f'標題：{note_to_delete["title"]}',
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text('刪除失敗 😢')
            
    except ValueError:
        await update.message.reply_text('❌ 請提供有效的數字')