"""
データソースの抽象基底クラス
後でスクレイピング等の追加データソースを実装可能にする
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
import pandas as pd


class DataSource(ABC):
    """データソース基底クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        データを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            pd.DataFrame: 日付をインデックスとするデータフレーム
        """
        pass
    
    @abstractmethod
    def get_latest(self) -> Dict[str, float]:
        """
        最新データを取得
        
        Returns:
            Dict[str, float]: 指標名と値の辞書
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """データソース名"""
        pass


class DataSourceError(Exception):
    """データソース関連のエラー"""
    pass
