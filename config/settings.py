"""
配置管理模組
"""
import os
from typing import Optional
from pathlib import Path

# 嘗試載入 .env 文件（本地開發用）
try:
    from dotenv import load_dotenv
    # 載入 .env 文件
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # 生產環境不需要 dotenv
    pass

class Settings:
    """應用配置"""
    
    # Bot 配置
    BOT_TOKEN: str = os.environ.get('BOT_TOKEN', '')
    ANTHROPIC_API_KEY: Optional[str] = os.environ.get('ANTHROPIC_API_KEY')
    
    # 資料庫配置
    DATABASE_URL: Optional[str] = os.environ.get('DATABASE_URL')
    
    # Claude 配置
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 2048
    CLAUDE_SYSTEM_PROMPT: str = (
        "你是 Aria，一個友善且樂於助人的 AI 助手。"
        "你會記住之前的對話內容，並提供連貫、有幫助的回答。\n\n"
        "你有以下工具可以使用：\n"
        "1. get_weather - 查詢城市天氣\n"
        "2. convert_currency - 轉換貨幣匯率\n"
        "3. save_note - 儲存筆記\n\n"
        "當用戶的需求適合使用這些工具時，請主動使用工具來提供更準確的資訊。\n"
        "使用工具後，簡短友善地說明結果即可，不需要重複工具已經提供的詳細資訊。"
    )
    
    # 對話歷史配置
    CONVERSATION_HISTORY_LIMIT: int = 10
    
    # 日誌配置
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> bool:
        """驗證必要配置是否存在"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN 未設置")
        return True
    
    @classmethod
    def fix_database_url(cls) -> Optional[str]:
        """修正 Railway 的 DATABASE_URL"""
        if cls.DATABASE_URL and cls.DATABASE_URL.startswith('postgres://'):
            return cls.DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        return cls.DATABASE_URL

settings = Settings()