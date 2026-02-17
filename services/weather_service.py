"""
天氣服務
"""
import requests
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WeatherService:
    """天氣查詢服務"""
    
    BASE_URL = "https://wttr.in"
    
    @staticmethod
    def get_weather(city: str) -> Optional[Dict]:
        """
        查詢城市天氣
        
        Args:
            city: 城市名稱
        
        Returns:
            天氣資料字典，失敗返回 None
        """
        try:
            url = f"{WeatherService.BASE_URL}/{city}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                
                return {
                    'city': city,
                    'temp_c': current['temp_C'],
                    'feels_like': current['FeelsLikeC'],
                    'humidity': current['humidity'],
                    'weather_desc': current['weatherDesc'][0]['value'],
                    'wind_speed': current['windspeedKmph']
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None

weather_service = WeatherService()