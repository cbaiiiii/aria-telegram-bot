"""
匯率服務
"""
import requests
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)

class CurrencyService:
    """匯率轉換服務"""
    
    BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    
    CURRENCIES = {
        'TWD': '台幣',
        'USD': '美金',
        'EUR': '歐元',
        'GBP': '英鎊',
        'JPY': '日圓',
        'CNY': '人民幣',
        'KRW': '韓元'
    }
    
    @staticmethod
    def convert(amount: float, from_currency: str) -> Optional[Dict]:
        """
        轉換匯率
        
        Args:
            amount: 金額
            from_currency: 來源貨幣代碼
        
        Returns:
            轉換結果字典，失敗返回 None
        """
        try:
            url = f"{CurrencyService.BASE_URL}/{from_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data['rates']
                
                results = {}
                for code, name in CurrencyService.CURRENCIES.items():
                    if code != from_currency and code in rates:
                        results[code] = {
                            'name': name,
                            'amount': amount * rates[code]
                        }
                
                return {
                    'from_currency': from_currency,
                    'from_amount': amount,
                    'results': results,
                    'date': data.get('date')
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Currency API error: {e}")
            return None

currency_service = CurrencyService()