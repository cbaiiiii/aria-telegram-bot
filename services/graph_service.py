"""
知識圖譜視覺化服務
"""
import io
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 設定中文字體（避免亂碼）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class GraphService:
    """知識圖譜視覺化服務"""
    
    @staticmethod
    def generate_graph_image(graph_data: Dict) -> io.BytesIO:
        """
        生成知識圖譜圖片
        
        Args:
            graph_data: 包含 nodes 和 edges 的字典
        
        Returns:
            圖片的 BytesIO 對象
        """
        try:
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])
            
            if not nodes:
                return None
            
            # 創建有向圖
            G = nx.Graph()
            
            # 添加節點
            for node in nodes:
                # 節點屬性：標題、標籤數量
                G.add_node(
                    node['id'],
                    title=node['title'],
                    tags=node.get('tags', []),
                    tag_count=len(node.get('tags', []))
                )
            
            # 添加邊
            link_edges = []
            tag_edges = []
            
            for edge in edges:
                G.add_edge(edge['source'], edge['target'])
                
                if edge['type'] == 'link':
                    link_edges.append((edge['source'], edge['target']))
                else:
                    tag_edges.append((edge['source'], edge['target']))
            
            # 設置圖片大小
            plt.figure(figsize=(16, 12))
            
            # 使用 spring layout（力導向布局，類似 Obsidian）
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            
            # 計算節點大小（基於連接數）
            node_sizes = []
            for node_id in G.nodes():
                degree = G.degree(node_id)
                size = 1000 + (degree * 300)  # 基礎大小 + 連接數加成
                node_sizes.append(size)
            
            # 計算節點顏色（基於標籤數量）
            node_colors = []
            for node_id in G.nodes():
                tag_count = G.nodes[node_id].get('tag_count', 0)
                # 顏色從淺藍到深藍
                color_intensity = min(1.0, 0.3 + (tag_count * 0.15))
                node_colors.append(color_intensity)
            
            # 繪製標籤關聯邊（虛線，淺色）
            if tag_edges:
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=tag_edges,
                    edge_color='#CCCCCC',
                    style='dashed',
                    width=1.5,
                    alpha=0.5
                )
            
            # 繪製連結邊（實線，深色）
            if link_edges:
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=link_edges,
                    edge_color='#4A90E2',
                    style='solid',
                    width=3,
                    alpha=0.8,
                    arrows=True,
                    arrowsize=20
                )
            
            # 繪製節點
            nx.draw_networkx_nodes(
                G, pos,
                node_size=node_sizes,
                node_color=node_colors,
                cmap=plt.cm.Blues,
                alpha=0.9,
                edgecolors='#2C3E50',
                linewidths=2
            )
            
            # 繪製標籤（節點標題）
            labels = {node_id: G.nodes[node_id]['title'] for node_id in G.nodes()}
            nx.draw_networkx_labels(
                G, pos,
                labels,
                font_size=10,
                font_weight='bold',
                font_color='#2C3E50'
            )
            
            # 設置標題和說明
            plt.title(
                '🧠 知識圖譜 (Knowledge Graph)',
                fontsize=20,
                fontweight='bold',
                pad=20
            )
            
            # 添加圖例
            legend_text = (
                f'📊 節點數：{len(nodes)}  |  '
                f'🔗 連結：{len(link_edges)}  |  '
                f'🏷️ 標籤關聯：{len(tag_edges)}'
            )
            plt.figtext(
                0.5, 0.02,
                legend_text,
                ha='center',
                fontsize=12,
                style='italic'
            )
            
            # 移除坐標軸
            plt.axis('off')
            plt.tight_layout()
            
            # 保存到 BytesIO
            buf = io.BytesIO()
            plt.savefig(
                buf,
                format='png',
                dpi=150,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            buf.seek(0)
            plt.close()
            
            logger.info(f"✅ 生成圖譜圖片：{len(nodes)} 節點，{len(edges)} 邊")
            return buf
        
        except Exception as e:
            logger.error(f"生成圖譜圖片失敗: {e}", exc_info=True)
            plt.close()
            return None
    
    @staticmethod
    def generate_simple_stats_image(graph_data: Dict) -> io.BytesIO:
        """
        生成簡單的統計圖表（當筆記數量少時）
        
        Args:
            graph_data: 包含 nodes 和 edges 的字典
        
        Returns:
            圖片的 BytesIO 對象
        """
        try:
            nodes = graph_data.get('nodes', [])
            
            if not nodes:
                return None
            
            # 統計標籤使用情況
            tag_counts = {}
            for node in nodes:
                for tag in node.get('tags', []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            if not tag_counts:
                return None
            
            # 創建圖表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # 標籤使用統計（柱狀圖）
            tags = list(tag_counts.keys())[:10]  # 最多顯示 10 個
            counts = [tag_counts[tag] for tag in tags]
            
            colors = plt.cm.Blues(range(len(tags)))
            ax1.barh(tags, counts, color=colors)
            ax1.set_xlabel('筆記數量', fontsize=12)
            ax1.set_title('🏷️ 標籤使用統計', fontsize=14, fontweight='bold')
            ax1.grid(axis='x', alpha=0.3)
            
            # 筆記創建時間統計（折線圖）
            dates = {}
            for node in nodes:
                date = node['created_at'][:10]  # YYYY-MM-DD
                dates[date] = dates.get(date, 0) + 1
            
            sorted_dates = sorted(dates.items())
            date_labels = [d[0] for d in sorted_dates]
            date_counts = [d[1] for d in sorted_dates]
            
            ax2.plot(date_labels, date_counts, marker='o', linewidth=2, markersize=8, color='#4A90E2')
            ax2.fill_between(range(len(date_counts)), date_counts, alpha=0.3, color='#4A90E2')
            ax2.set_xlabel('日期', fontsize=12)
            ax2.set_ylabel('筆記數量', fontsize=12)
            ax2.set_title('📅 筆記創建趨勢', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 保存到 BytesIO
            buf = io.BytesIO()
            plt.savefig(
                buf,
                format='png',
                dpi=150,
                bbox_inches='tight',
                facecolor='white'
            )
            buf.seek(0)
            plt.close()
            
            return buf
        
        except Exception as e:
            logger.error(f"生成統計圖表失敗: {e}", exc_info=True)
            plt.close()
            return None

# 全局實例
graph_service = GraphService()