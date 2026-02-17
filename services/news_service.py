"""
新聞服務
"""
import feedparser
from typing import List, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NewsService:
    """新聞訂閱服務 (使用 RSS)"""
    
    RSS_FEEDS = {
        'technology': [
            'https://feeds.bbci.co.uk/news/technology/rss.xml',
            'http://feeds.arstechnica.com/arstechnica/index',
        ],
        'world': [
            'https://feeds.bbci.co.uk/news/world/rss.xml',
        ],
        'business': [
            'https://feeds.bbci.co.uk/news/business/rss.xml',
        ],
        'science': [
            'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
        ]
    }
    
    @staticmethod
    def fetch_news(category: str = 'all', max_items: int = 5) -> Optional[List[Dict]]:
        """
        取得新聞
        
        Args:
            category: 新聞類別
            max_items: 最多幾則
        
        Returns:
            新聞列表
        """
        try:
            news_list = []
            
            # 決定 RSS 源
            if category == 'all':
                feeds = [feed for feeds in NewsService.RSS_FEEDS.values() for feed in feeds]
            else:
                feeds = NewsService.RSS_FEEDS.get(category, [])
            
            # 抓取新聞
            for feed_url in feeds[:2]:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:3]:
                        news_list.append({
                            'title': entry.get('title', ''),
                            'summary': entry.get('summary', '')[:150] + '...' if entry.get('summary') else '',
                            'link': entry.get('link', ''),
                            'published': entry.get('published', ''),
                            'source': feed.feed.get('title', 'Unknown')
                        })
                except Exception as e:
                    logger.error(f"RSS parse error {feed_url}: {e}")
                    continue
            
            return news_list[:max_items]
        
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return None

news_service = NewsService()