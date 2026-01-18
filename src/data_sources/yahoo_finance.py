"""
Yahoo Financeからの価格データ取得
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
from .base import DataSource, DataSourceError


class YahooFinanceSource(DataSource):
    """Yahoo Financeデータソース"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.symbols = config.get('symbols', {
            'gold': 'GC=F',
            'silver': 'SI=F'
        })
    
    @property
    def name(self) -> str:
        return "Yahoo Finance"
    
    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        金と銀の価格データを取得
        
        Returns:
            DataFrame with columns: gold_price, silver_price, gold_silver_ratio
        """
        try:
            # 金価格の取得
            gold = yf.download(
                self.symbols['gold'],
                start=start_date,
                end=end_date,
                progress=False
            )['Close']
            
            # 銀価格の取得
            silver = yf.download(
                self.symbols['silver'],
                start=start_date,
                end=end_date,
                progress=False
            )['Close']
            
            # データフレームの結合
            df = pd.DataFrame({
                'gold_price': gold,
                'silver_price': silver
            })
            
            # 金銀比価の計算
            df['gold_silver_ratio'] = df['gold_price'] / df['silver_price']
            
            # 欠損値の処理（前方埋め）
            df = df.fillna(method='ffill')
            
            return df
            
        except Exception as e:
            raise DataSourceError(f"Yahoo Finance data fetch failed: {e}")
    
    def get_latest(self) -> Dict[str, float]:
        """最新の金銀価格と比価を取得"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # 直近1週間
            
            df = self.fetch(start_date, end_date)
            
            if df.empty:
                raise DataSourceError("No data available")
            
            latest = df.iloc[-1]
            
            return {
                'gold_price': float(latest['gold_price']),
                'silver_price': float(latest['silver_price']),
                'gold_silver_ratio': float(latest['gold_silver_ratio']),
                'date': df.index[-1].strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            raise DataSourceError(f"Failed to get latest data: {e}")
    
    def get_dollar_index(self, start_date: datetime, end_date: datetime) -> pd.Series:
        """ドルインデックスを取得（オプション）"""
        try:
            dxy = yf.download(
                'DX-Y.NYB',
                start=start_date,
                end=end_date,
                progress=False
            )['Close']
            return dxy
        except Exception as e:
            raise DataSourceError(f"Dollar index fetch failed: {e}")
