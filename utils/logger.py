"""
日誌配置模組
"""
import logging
import sys

def setup_logger(name: str) -> logging.Logger:
    """
    設置並返回一個配置好的 logger
    
    Args:
        name: Logger 名稱（通常使用 __name__）
    
    Returns:
        配置好的 Logger 實例
    """
    logger = logging.getLogger(name)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 設置日誌級別
    logger.setLevel(logging.INFO)
    
    # 創建 console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 創建 formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 將 formatter 添加到 handler
    console_handler.setFormatter(formatter)
    
    # 將 handler 添加到 logger
    logger.addHandler(console_handler)
    
    # 防止日誌傳播到根 logger（避免重複輸出）
    logger.propagate = False
    
    return logger