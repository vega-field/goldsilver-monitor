from typing import Dict
import pandas as pd
import numpy as np

class FragilityAnalyzer:
    def __init__(self, window_days: int = 30):
        self.window_days = window_days

    def analyze(self, price_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        price_data: dict of ticker -> DataFrame (must contain 'Close')
        returns: a result dict with fragility scores and diagnostics
        """
        result = {}
        # 換算可能なペアが存在するか確認
        if not price_data:
            return {"error": "no price data"}

        # 例として GC=F と SI=F が揃っている場合に比率とボラティリティを計算
        gold_key = next((k for k in price_data if "GC" in k or "Gold" in k), None)
        silver_key = next((k for k in price_data if "SI" in k or "Silver" in k), None)

        if gold_key and silver_key:
            g = price_data[gold_key]["Close"].dropna()
            s = price_data[silver_key]["Close"].dropna()
            # 日付で合わせる
            df = pd.DataFrame({"gold": g, "silver": s}).dropna()
            df["ratio"] = df["gold"] / df["silver"]
            # 移動平均とボラティリティ
            df["ratio_ma"] = df["ratio"].rolling(self.window_days).mean()
            df["ratio_std"] = df["ratio"].rolling(self.window_days).std()
            latest = df.iloc[-1].to_dict()
            fragility_score = float(latest.get("ratio_std", np.nan))  # 単純な例
            result = {
                "gold_ticker": gold_key,
                "silver_ticker": silver_key,
                "latest_ratio": float(latest.get("ratio", np.nan)),
                "ratio_ma": float(latest.get("ratio_ma", np.nan)),
                "ratio_std": float(latest.get("ratio_std", np.nan)),
                "fragility_score": fragility_score,
            }
        else:
            result = {"error": "required tickers not found in price_data"}

        return result