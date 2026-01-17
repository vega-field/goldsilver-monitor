from typing import List, Dict
import pandas as pd

try:
    import yfinance as yf
except Exception:
    yf = None

from .base import DataSource

class YahooFinanceSource(DataSource):
    def __init__(self, tickers: List[str], interval: str = "1d"):
        self.tickers = tickers
        self.interval = interval

    def fetch(self) -> Dict[str, pd.DataFrame]:
        if yf is None:
            raise RuntimeError("yfinance is not installed. See requirements.txt")
        data = {}
        for t in self.tickers:
            df = yf.download(t, period="60d", interval=self.interval, progress=False)
            if not df.empty:
                data[t] = df
        return data