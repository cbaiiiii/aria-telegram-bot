"""
Claude AI 服務（支援 Tool Use）
"""
from typing import List, Dict, Optional, Any
from anthropic import Anthropic
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ClaudeService:
    """Claude AI 服務類"""
    
    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("✅ Claude service initialized")
        else:
            logger.warning("⚠️ ANTHROPIC_API_KEY not set")
    
    @property
    def is_available(self) -> bool:
        """檢查服務是否可用"""
        return self.client is not None
    
    # 定義可用的工具
    TOOLS = [
        {
            "name": "get_weather",
            "description": "查詢指定城市的當前天氣資訊，包括溫度、濕度、天氣狀況、風速等。支援中英文城市名稱。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名稱，例如：台北、台中、Taipei、Tokyo、New York"
                    }
                },
                "required": ["city"]
            }
        },
        {
            "name": "convert_currency",
            "description": "轉換貨幣匯率，支援主要貨幣之間的即時匯率轉換",
            "input_schema": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "要轉換的金額數字"
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "來源貨幣代碼（大寫），例如：USD（美金）、TWD（台幣）、EUR（歐元）、GBP（英鎊）、JPY（日圓）、CNY（人民幣）、KRW（韓元）"
                    }
                },
                "required": ["amount", "from_currency"]
            }
        },
        {
            "name": "save_note",
            "description": "儲存用戶的筆記、待辦事項或重要資訊到資料庫。支援使用 #標籤 來分類，以及 [[筆記標題]] 來連結其他筆記",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "筆記標題，簡短描述筆記內容"
                    },
                    "content": {
                        "type": "string",
                        "description": "筆記的詳細內容。可以包含 #標籤 來分類（例如：#工作 #重要），也可以用 [[其他筆記標題]] 來建立連結"
                    }
                },
                "required": ["title", "content"]
            }
        },
        {
            "name": "fetch_daily_news",
            "description": "取得今日國際新聞摘要。從 BBC、Reuters 等可靠來源抓取最新新聞,包含科技、國際、商業等類別",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["all", "technology", "world", "business", "science"],
                        "description": "新聞類別",
                        "default": "all"
                    },
                    "max_items": {
                        "type": "integer",
                        "description": "最多幾則新聞 (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    }
                }
            }
        },
        {
            "name": "search_arxiv_papers",
            "description": """
            在 arXiv 搜尋學術論文。
            可以用關鍵字搜尋特定主題的論文,也可以取得某類別的最新論文。
            支援 AI、機器學習、電腦視覺、自然語言處理等領域。
            返回論文標題、作者、摘要、PDF 連結等資訊。
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜尋關鍵字,例如: 'vanna', 'transformer', 'diffusion model', 'GPT'。留空則返回最新論文",
                        "default": ""
                    },
                    "category": {
                        "type": "string",
                        "enum": ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE", "all"],
                        "description": """
                        論文類別:
                        - cs.AI: 人工智慧
                        - cs.LG: 機器學習
                        - cs.CV: 電腦視覺
                        - cs.CL: 自然語言處理
                        - cs.NE: 神經網路
                        - all: 所有 AI 相關類別
                        """,
                        "default": "all"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回幾篇論文 (1-10),預設 3",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 3
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "date"],
                        "description": "排序方式: relevance(按相關性) 或 date(按發布日期)",
                        "default": "relevance"
                    }
                }
            }
        },
        {
            "name": "generate_language_lesson",
            "description": "生成每日語言學習內容,包含實用句子、單字、文法解釋、例句等",
            "input_schema": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["english", "japanese", "korean"],
                        "description": "學習語言",
                        "default": "english"
                    },
                    "level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "難度級別",
                        "default": "intermediate"
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["daily_life", "business", "travel", "technology", "random"],
                        "description": "主題",
                        "default": "random"
                    }
                }
            }
        },
        {
            "name": "research_topic",
            "description": """
            深度研究某個主題,從多個來源收集資訊並生成綜合報告。
            
            會搜尋:
            1. arXiv 學術論文
            2. 網路文章和文件
            3. GitHub 專案 (如果相關)
            4. 技術部落格
            
            然後綜合分析,生成包含以下內容的報告:
            - 主題概述
            - 核心概念
            - 主要技術/方法
            - 應用場景
            - 相關資源連結
            
            適合用於:快速了解新技術、工具、研究領域
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "研究主題,例如: 'Vanna', 'LangChain', 'Stable Diffusion', 'RLHF'"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["overview", "technical", "application", "comparison"],
                        "description": """
                        研究重點:
                        - overview: 全面概述 (適合初學者)
                        - technical: 技術細節 (適合開發者)
                        - application: 應用案例 (適合產品經理)
                        - comparison: 與類似技術比較
                        """,
                        "default": "overview"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["brief", "detailed"],
                        "description": "報告深度: brief(簡短摘要) 或 detailed(詳細報告)",
                        "default": "detailed"
                    }
                },
                "required": ["topic"]
            }
        }
    ]
    
    def chat(self, messages: List[Dict[str, str]], 
             system_prompt: Optional[str] = None,
             use_tools: bool = True) -> Dict[str, Any]:
        """
        與 Claude 對話（支援工具調用）
        
        Args:
            messages: 訊息列表
            system_prompt: 系統提示詞
            use_tools: 是否啟用工具調用
        
        Returns:
            包含 text 和 tool_calls 的字典
        """
        if not self.is_available:
            logger.error("Claude service not available")
            return {"text": None, "tool_calls": [], "stop_reason": None}
        
        try:
            kwargs = {
                "model": settings.CLAUDE_MODEL,
                "max_tokens": settings.CLAUDE_MAX_TOKENS,
                "system": system_prompt or settings.CLAUDE_SYSTEM_PROMPT,
                "messages": messages
            }
            
            # 如果啟用工具，添加 tools 參數
            if use_tools:
                kwargs["tools"] = self.TOOLS
            
            response = self.client.messages.create(**kwargs)
            
            # 解析回應
            text_content = ""
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            return {
                "text": text_content if text_content else None,
                "tool_calls": tool_calls,
                "stop_reason": response.stop_reason
            }
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {"text": None, "tool_calls": [], "stop_reason": None}

# 全局 Claude 服務實例
claude_service = ClaudeService()