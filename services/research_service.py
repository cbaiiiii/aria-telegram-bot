"""
研究服務 - 綜合多來源資訊
"""
import requests
from typing import Dict, List, Optional
from services.arxiv_service import arxiv_service
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ResearchService:
    """綜合研究服務"""
    
    @staticmethod
    def search_web_articles(query: str, max_results: int = 3) -> List[Dict]:
        """
        搜尋網路文章 (使用 DuckDuckGo 或其他免費 API)
        
        Args:
            query: 搜尋關鍵字
            max_results: 最多幾篇
        
        Returns:
            文章列表
        """
        try:
            # 使用 DuckDuckGo Instant Answer API (免費)
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                # 取得摘要
                if data.get('AbstractText'):
                    articles.append({
                        'title': data.get('Heading', query),
                        'snippet': data.get('AbstractText', ''),
                        'url': data.get('AbstractURL', ''),
                        'source': data.get('AbstractSource', 'Web')
                    })
                
                # 取得相關主題
                for topic in data.get('RelatedTopics', [])[:max_results-1]:
                    if 'Text' in topic:
                        articles.append({
                            'title': topic.get('Text', '')[:100],
                            'snippet': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'source': 'DuckDuckGo'
                        })
                
                return articles
            
            return []
        
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    @staticmethod
    def search_github(query: str) -> Optional[Dict]:
        """
        搜尋 GitHub 專案 (免費,無需 token)
        
        Args:
            query: 專案名稱
        
        Returns:
            專案資訊
        """
        try:
            # GitHub API (無需認證,每小時 60 次請求)
            url = f"https://api.github.com/search/repositories"
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 1
            }
            
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['items']:
                    repo = data['items'][0]
                    return {
                        'name': repo['full_name'],
                        'description': repo.get('description', 'No description'),
                        'stars': repo['stargazers_count'],
                        'url': repo['html_url'],
                        'language': repo.get('language', 'Unknown'),
                        'topics': repo.get('topics', [])
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return None
    
    @staticmethod
    def research_topic(topic: str, focus: str = "overview", depth: str = "detailed") -> Dict:
        """
        綜合研究主題
        
        Args:
            topic: 研究主題
            focus: 研究重點
            depth: 報告深度
        
        Returns:
            包含所有來源資訊的字典
        """
        logger.info(f"Researching: {topic} (focus={focus}, depth={depth})")
        
        research_data = {
            'topic': topic,
            'focus': focus,
            'papers': [],
            'web_articles': [],
            'github': None
        }
        
        # 1. 搜尋論文
        papers = arxiv_service.search_papers(
            query=topic,
            max_results=3 if depth == "detailed" else 2
        )
        if papers:
            research_data['papers'] = papers
            logger.info(f"Found {len(papers)} papers")
        
        # 2. 搜尋網路文章
        articles = ResearchService.search_web_articles(
            query=topic,
            max_results=3 if depth == "detailed" else 2
        )
        if articles:
            research_data['web_articles'] = articles
            logger.info(f"Found {len(articles)} articles")
        
        # 3. 搜尋 GitHub
        github_repo = ResearchService.search_github(topic)
        if github_repo:
            research_data['github'] = github_repo
            logger.info(f"Found GitHub: {github_repo['name']}")
        
        return research_data

research_service = ResearchService()