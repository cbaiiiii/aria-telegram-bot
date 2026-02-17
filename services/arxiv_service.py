"""
arXiv 論文服務
"""
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ArxivService:
    """arXiv 論文搜尋服務"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    @staticmethod
    def search_papers(
        query: str = "",
        category: str = "all",
        max_results: int = 3,
        sort_by: str = "relevance"
    ) -> Optional[List[Dict]]:
        """
        搜尋 arXiv 論文
        
        Args:
            query: 搜尋關鍵字 (可為空)
            category: 論文類別 (cs.AI, cs.LG 等)
            max_results: 返回數量 (1-10)
            sort_by: 排序方式 (relevance 或 date)
        
        Returns:
            論文列表,每篇包含 id, title, authors, summary, published, pdf_url, web_url
        """
        try:
            # 建構搜尋查詢
            if query:
                # 有關鍵字:在標題和摘要中搜尋
                search_query = f'(ti:"{query}" OR abs:"{query}")'
                
                # 如果指定類別,加上類別限制
                if category != "all":
                    search_query += f' AND cat:{category}'
                else:
                    # 限制在 AI 相關類別
                    search_query += ' AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CV OR cat:cs.CL OR cat:cs.NE)'
            else:
                # 無關鍵字:只按類別取最新
                if category == 'all':
                    search_query = 'cat:cs.AI OR cat:cs.LG OR cat:cs.CV OR cat:cs.CL OR cat:cs.NE'
                else:
                    search_query = f'cat:{category}'
            
            # API 參數
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance' if sort_by == 'relevance' else 'submittedDate',
                'sortOrder': 'descending'
            }
            
            logger.info(f"arXiv search: query='{query}', category={category}, max={max_results}")
            
            response = requests.get(ArxivService.BASE_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                # 解析 XML
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                papers = []
                entries = root.findall('atom:entry', ns)
                
                if not entries:
                    logger.warning("No papers found")
                    return None
                
                for entry in entries:
                    try:
                        # 提取論文資訊
                        title = entry.find('atom:title', ns).text.strip()
                        summary = entry.find('atom:summary', ns).text.strip()
                        
                        # 摘要截斷到 300 字
                        if len(summary) > 300:
                            summary = summary[:300] + '...'
                        
                        # 作者 (最多 3 位)
                        authors = [a.find('atom:name', ns).text 
                                 for a in entry.findall('atom:author', ns)[:3]]
                        
                        # 如果作者超過 3 位,加上 et al.
                        if len(entry.findall('atom:author', ns)) > 3:
                            authors.append('et al.')
                        
                        # 發布日期
                        published = entry.find('atom:published', ns).text[:10]
                        
                        # arXiv ID
                        arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
                        
                        papers.append({
                            'id': arxiv_id,
                            'title': title,
                            'authors': authors,
                            'summary': summary,
                            'published': published,
                            'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                            'web_url': f"https://arxiv.org/abs/{arxiv_id}"
                        })
                    
                    except Exception as e:
                        logger.error(f"Parse entry error: {e}")
                        continue
                
                logger.info(f"✅ Found {len(papers)} papers")
                return papers if papers else None
            
            else:
                logger.error(f"arXiv API error: status {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"arXiv search error: {e}", exc_info=True)
            return None

arxiv_service = ArxivService()