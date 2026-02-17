"""
資料庫連線管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from config.settings import settings
from utils.logger import setup_logger
from database.models import Base

logger = setup_logger(__name__)

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """初始化資料庫連線"""
        if self._initialized:
            return True
        
        database_url = settings.fix_database_url()
        
        if not database_url:
            logger.warning("⚠️ DATABASE_URL 未設置，資料庫功能將無法使用")
            return False
        
        try:
            self.engine = create_engine(database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # 創建所有表格
            Base.metadata.create_all(bind=self.engine)
            
            self._initialized = True
            logger.info("✅ 資料庫連線成功")
            return True
        except Exception as e:
            logger.error(f"❌ 資料庫連線失敗: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """取得資料庫 session（使用 context manager）"""
        if not self._initialized or self.SessionLocal is None:
            yield None
            return
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"資料庫操作錯誤: {e}")
            raise
        finally:
            session.close()
    
    @property
    def is_connected(self) -> bool:
        """檢查是否已連線"""
        return self._initialized and self.engine is not None

# 全局資料庫管理器實例
db_manager = DatabaseManager()