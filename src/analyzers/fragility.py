"""
金銀市場の脆弱性分析エンジン
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta


class FragilityAnalyzer:
    """市場脆弱性分析クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get('fragility_thresholds', {})
        self.stats_config = config.get('statistics', {})
        
        # 統計計算用のパラメータ
        self.lookback = self.stats_config.get('lookback_period', 252)
        self.zscore_window = self.stats_config.get('zscore_window', 252)
    
    def calculate_zscore(self, series: pd.Series, window: int = None) -> pd.Series:
        """Z-scoreを計算"""
        if window is None:
            window = self.zscore_window
        
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        zscore = (series - rolling_mean) / rolling_std
        return zscore
    
    def calculate_percentile(self, series: pd.Series, window: int = None) -> pd.Series:
        """パーセンタイルを計算（0-100）"""
        if window is None:
            window = self.lookback
        
        def percentile_rank(x):
            if len(x) < 2:
                return 50.0
            return (x.rank().iloc[-1] - 1) / (len(x) - 1) * 100
        
        return series.rolling(window=window).apply(percentile_rank, raw=False)
    
    def analyze_gold_silver_ratio(self, ratio_series: pd.Series) -> Dict[str, Any]:
        """金銀比価の分析"""
        current_ratio = float(ratio_series.iloc[-1])
        
        # 統計値の計算
        zscore = float(self.calculate_zscore(ratio_series).iloc[-1])
        percentile = float(self.calculate_percentile(ratio_series).iloc[-1])
        
        # 移動平均からの乖離
        ma_20 = ratio_series.rolling(20).mean().iloc[-1]
        ma_50 = ratio_series.rolling(50).mean().iloc[-1]
        deviation_from_ma20 = (current_ratio - ma_20) / ma_20 * 100
        
        # 脆弱性レベルの判定
        fragility_level = self._assess_ratio_fragility(
            current_ratio, zscore, percentile
        )
        
        return {
            'current_value': current_ratio,
            'zscore': zscore,
            'percentile': percentile,
            'ma_20': float(ma_20),
            'ma_50': float(ma_50),
            'deviation_from_ma20': float(deviation_from_ma20),
            'fragility_level': fragility_level,
            'interpretation': self._interpret_ratio(current_ratio, zscore)
        }
    
    def _assess_ratio_fragility(self, ratio: float, zscore: float, 
                                 percentile: float) -> str:
        """金銀比価の脆弱性レベルを評価"""
        thresholds = self.thresholds.get('gold_silver_ratio', {})
        zscore_thresholds = self.thresholds.get('zscore', {})
        
        # CRITICAL条件
        if (ratio >= thresholds.get('critical_high', 85) or 
            ratio <= thresholds.get('critical_low', 45) or
            abs(zscore) >= zscore_thresholds.get('extreme', 2.0)):
            return 'CRITICAL'
        
        # HIGH条件
        if (ratio >= thresholds.get('high', 80) or 
            ratio <= thresholds.get('low', 50) or
            abs(zscore) >= zscore_thresholds.get('high', 1.5)):
            return 'HIGH'
        
        # MODERATE条件
        if abs(zscore) >= zscore_thresholds.get('moderate', 1.0):
            return 'MODERATE'
        
        return 'LOW'
    
    def _interpret_ratio(self, ratio: float, zscore: float) -> str:
        """金銀比価の解釈"""
        thresholds = self.thresholds.get('gold_silver_ratio', {})
        
        if ratio >= thresholds.get('critical_high', 85):
            return f"極端な高比価（{ratio:.1f}）- 銀の歴史的割安、反転リスク高"
        elif ratio >= thresholds.get('high', 80):
            return f"高比価圏（{ratio:.1f}）- 銀が割安傾向"
        elif ratio <= thresholds.get('critical_low', 45):
            return f"極端な低比価（{ratio:.1f}）- 銀の割高、調整リスク高"
        elif ratio <= thresholds.get('low', 50):
            return f"低比価圏（{ratio:.1f}）- 銀が割高傾向"
        else:
            return f"正常範囲（{ratio:.1f}）"
    
    def analyze_price_momentum(self, price_series: pd.Series, 
                                name: str = 'price') -> Dict[str, Any]:
        """価格モメンタム分析"""
        # 変化率の計算
        change_1d = float((price_series.iloc[-1] / price_series.iloc[-2] - 1) * 100)
        change_5d = float((price_series.iloc[-1] / price_series.iloc[-6] - 1) * 100)
        change_20d = float((price_series.iloc[-1] / price_series.iloc[-21] - 1) * 100)
        
        # ボラティリティ
        volatility_20d = float(price_series.pct_change().rolling(20).std() * np.sqrt(252) * 100)
        
        # 異常値判定
        is_extreme_daily = abs(change_1d) >= self.thresholds.get('price_change', {}).get('daily_extreme', 5.0)
        is_extreme_weekly = abs(change_5d) >= self.thresholds.get('price_change', {}).get('weekly_extreme', 10.0)
        
        return {
            'name': name,
            'current_price': float(price_series.iloc[-1]),
            'change_1d_pct': change_1d,
            'change_5d_pct': change_5d,
            'change_20d_pct': change_20d,
            'volatility_20d_annualized': volatility_20d,
            'is_extreme_daily': is_extreme_daily,
            'is_extreme_weekly': is_extreme_weekly
        }
    
    def detect_composite_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """複合シグナルの検出"""
        signals = []
        
        # シグナル1: 高比価 × 価格下落
        if (market_data.get('ratio_fragility', 'LOW') in ['HIGH', 'CRITICAL'] and
            market_data['gold_silver_ratio']['current_value'] > 80 and
            market_data.get('silver_momentum', {}).get('change_5d_pct', 0) < -3):
            signals.append({
                'type': 'HIGH_RATIO_PRICE_DECLINE',
                'severity': 'HIGH',
                'message': '高比価継続中に銀価格が下落 - 売り圧力の継続'
            })
        
        # シグナル2: 低比価 × 価格上昇
        if (market_data.get('ratio_fragility', 'LOW') in ['HIGH', 'CRITICAL'] and
            market_data['gold_silver_ratio']['current_value'] < 55 and
            market_data.get('silver_momentum', {}).get('change_5d_pct', 0) > 5):
            signals.append({
                'type': 'LOW_RATIO_PRICE_SURGE',
                'severity': 'MODERATE',
                'message': '低比価圏で銀価格が急騰 - 過熱感、調整リスク'
            })
        
        # シグナル3: 極端なZ-score
        if abs(market_data['gold_silver_ratio'].get('zscore', 0)) > 2.0:
            signals.append({
                'type': 'EXTREME_STATISTICAL_DEVIATION',
                'severity': 'CRITICAL',
                'message': f"統計的異常値検知（Z-score: {market_data['gold_silver_ratio']['zscore']:.2f}）"
            })
        
        return signals
    
    def generate_fragility_score(self, market_data: Dict[str, Any]) -> int:
        """総合脆弱性スコアを計算（0-100）"""
        score = 0
        
        # 金銀比価の寄与（最大40点）
        ratio_level = market_data.get('ratio_fragility', 'LOW')
        ratio_scores = {'CRITICAL': 40, 'HIGH': 30, 'MODERATE': 20, 'LOW': 10}
        score += ratio_scores.get(ratio_level, 10)
        
        # 価格変動の寄与（最大30点）
        if market_data.get('silver_momentum', {}).get('is_extreme_weekly', False):
            score += 30
        elif market_data.get('silver_momentum', {}).get('is_extreme_daily', False):
            score += 20
        
        # 統計的異常度の寄与（最大30点）
        zscore = abs(market_data['gold_silver_ratio'].get('zscore', 0))
        if zscore >= 2.0:
            score += 30
        elif zscore >= 1.5:
            score += 20
        elif zscore >= 1.0:
            score += 10
        
        return min(score, 100)
