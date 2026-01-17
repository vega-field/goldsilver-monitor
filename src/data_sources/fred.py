from typing import List, Dict
import pandas as pd
import os

try:
    from fredapi import Fred
except Exception:
    Fred = None

from .base import DataSource

class FREDSource(DataSource):
    def __init__(self, series: List[str], api_key: str = None):
        self.series = series
        self.api_key = api_key or os.environ.get("FRED_API_KEY")

    def fetch(self) -> Dict[str, pd.Series]:
        if Fred is None:
            raise RuntimeError("fredapi is not installed. See requirements.txt")
        fred = Fred(api_key=self.api_key)
        data = {}
        for s in self.series:
            data[s] = fred.get_series(s)
        return data