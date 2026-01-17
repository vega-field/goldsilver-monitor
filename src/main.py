import os
import logging
import yaml
from loguru import logger

from src.data_sources.yahoo_finance import YahooFinanceSource
from src.analyzers.fragility import FragilityAnalyzer
from src.alerts.obsidian import ObsidianAlert

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config_path = os.environ.get("CONFIG_PATH", "./config/config.yaml")
    config = load_config(config_path)

    logger.info("Config loaded from {}", config_path)

    # データ取得
    if config.get("data_sources", {}).get("yahoo", {}).get("enabled", False):
        ys_cfg = config["data_sources"]["yahoo"]
        ysrc = YahooFinanceSource(tickers=ys_cfg.get("tickers", []))
        prices = ysrc.fetch()
    else:
        prices = {}

    # 解析
    fa_cfg = config.get("analyzers", {}).get("fragility", {})
    analyzer = FragilityAnalyzer(window_days=fa_cfg.get("window_days", 30))
    result = analyzer.analyze(prices)

    # アラート
    alert_cfg = config.get("alerts", {}).get("obsidian", {})
    if alert_cfg.get("enabled", False):
        obs = ObsidianAlert(vault_path=alert_cfg.get("vault_path"))
        obs.send(result)

    logger.info("Run complete. Result: {}", result)

if __name__ == "__main__":
    main()