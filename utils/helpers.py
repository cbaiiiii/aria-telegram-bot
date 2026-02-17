"""
輔助函數模組
"""
from typing import List
from datetime import datetime

def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """
    將長訊息分割成多個部分
    
    Args:
        text: 要分割的文字
        max_length: 每段的最大長度（Telegram 限制 4096）
    
    Returns:
        分割後的文字列表
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # 按行分割
    lines = text.split('\n')
    
    for line in lines:
        # 如果單行就超過限制，強制分割
        if len(line) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # 分割長行
            for i in range(0, len(line), max_length):
                chunks.append(line[i:i+max_length])
            continue
        
        # 檢查加入這行後是否超過限制
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
    
    # 添加最後一個 chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化日期時間
    
    Args:
        dt: datetime 對象
        format_str: 格式字串
    
    Returns:
        格式化後的字串
    """
    return dt.strftime(format_str)

def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    截斷文字並添加後綴
    
    Args:
        text: 要截斷的文字
        max_length: 最大長度
        suffix: 後綴（預設為 '...'）
    
    Returns:
        截斷後的文字
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def sanitize_markdown(text: str) -> str:
    """
    清理 Markdown 特殊字符（用於 Telegram）
    
    Args:
        text: 要清理的文字
    
    Returns:
        清理後的文字
    """
    # Telegram Markdown 需要轉義的字符
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def extract_command_args(text: str, command: str) -> str:
    """
    從訊息中提取命令參數
    
    Args:
        text: 完整訊息文字
        command: 命令名稱（不含 /）
    
    Returns:
        參數文字
    """
    # 移除命令部分
    prefix = f'/{command}'
    if text.startswith(prefix):
        args = text[len(prefix):].strip()
        return args
    return text

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（bytes）
    
    Returns:
        格式化後的字串（如 "1.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def calculate_days_between(start_date: datetime, end_date: datetime = None) -> int:
    """
    計算兩個日期之間的天數
    
    Args:
        start_date: 開始日期
        end_date: 結束日期（預設為現在）
    
    Returns:
        天數
    """
    if end_date is None:
        end_date = datetime.utcnow()
    
    delta = end_date - start_date
    return delta.days

def is_valid_url(url: str) -> bool:
    """
    簡單的 URL 驗證
    
    Args:
        url: 要驗證的 URL
    
    Returns:
        是否為有效 URL
    """
    import re
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None