from abc import ABC, abstractmethod

class DataSource(ABC):
    @abstractmethod
    def fetch(self):
        """データを取得して標準化された形式（例: dict[ticker]=DataFrame）で返す"""
        raise NotImplementedError
