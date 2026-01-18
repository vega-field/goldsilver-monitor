"""
FRED (Federal Reserve Economic Data) からのマクロ指標取得
"""

from fredapi import Fred
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import os
from .base import DataSource, DataSourceError


class FREDSource(DataSource):
    """FREDデータソース"""
    
    def __init__(self, config: Dict[str, Any], api_key: Optional[str] = None):
        super().__init__(config)
        
        # API キーの取得（環境変数 or 引数）
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        if not self.api_key:
            raise DataSourceError("FRED API key is required")
        
        self.fred = Fred(api_key=self.api_key)
        self.indicators = config.get('indicators', {})
    
    @property
    def name(self) -> str:
        return "FRED"
    
    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        マクロ経済指標を取得
        
        Returns:
            DataFrame with columns: real_rate, pmi, dollar_index, etc.
        """
        try:
            data = {}
            
            # 各指標を取得
            for name, series_id in self.indicators.items():
                try:
                    series = self.fred.get_series(
                        series_id,
                        observation_start=start_date,
                        observation_end=end_date
                    )
                    data[name] = series
                except Exception as e:
                    print(f"Warning: Failed to fetch {name} ({series_id}): {e}")
                    continue
            
            if not data:
                raise DataSourceError("No FRED data could be retrieved")
            
            # データフレームに結合
            df = pd.DataFrame(data)
            
            # 実質金利の計算（10年国債利回り - ブレークイーブン・インフレ率）
            if 'treasury_10y' in df.columns and 'breakeven_10y' in df.columns:
                df['real_rate'] = df['treasury_10y'] - df['breakeven_10y']
            elif 'tips_10y' in df.columns:
                df['real_rate'] = df['tips_10y']
            
            # 欠損値の処理
            df = df.fillna(method='ffill')
            
            return df
            
        except Exception as e:
            raise DataSourceError(f"FRED data fetch failed: {e}")
    
    def get_latest(self) -> Dict[str, float]:
        """最新のマクロ指標を取得"""
        try:
            latest_data = {}
            
            for name, series_id in self.indicators.items():
                try:
                    series = self.fred.get_series(series_id)
                    latest_data[name] = float(series.iloc[-1])
                except Exception as e:
                    print(f"Warning: Failed to get latest {name}: {e}")
                    continue
            
            # 実質金利の計算
            if 'treasury_10y' in latest_data and 'breakeven_10y' in latest_data:
                latest_data['real_rate'] = (
                    latest_data['treasury_10y'] - latest_data['breakeven_10y']
                )
            
            return latest_data
            
        except Exception as e:
            raise DataSourceError(f"Failed to get latest FRED data: {e}")
    
    def get_series(self, series_id: str, start_date: datetime, 
                   end_date: datetime) -> pd.Series:
        """個別のFREDシリーズを取得（汎用メソッド）"""
        try:
            return self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
        except Exception as e:
            raise DataSourceError(f"Failed to fetch series {series_id}: {e}")
