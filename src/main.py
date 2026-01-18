"""
金銀市場脆弱性監視システム メインプログラム
"""

import os
import sys
import yaml
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging

from data_sources import YahooFinanceSource, FREDSource, DataSourceError
from analyzers import FragilityAnalyzer
from alerts import ObsidianReporter
from db_manager import DatabaseManager, rotate_logs


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class GoldSilverMonitor:
    """金銀市場監視メインクラス"""
    
    def __init__(self, config_path: str = '/app/config/config.yaml'):
        """初期化"""
        logger.info("Initializing Gold-Silver Monitor...")
        
        # 設定ファイルの読み込み
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # データベースの初期化
        self.db_path = '/data/market_data.db'
        self._init_database()
        
        # データソースの初期化
        self.yahoo = YahooFinanceSource(
            self.config['data_sources']['yahoo_finance']
        )
        
        try:
            self.fred = FREDSource(
                self.config['data_sources']['fred'],
                api_key=os.getenv('FRED_API_KEY')
            )
        except DataSourceError as e:
            logger.warning(f"FRED initialization failed: {e}")
            self.fred = None
        
        # 分析エンジンの初期化
        self.analyzer = FragilityAnalyzer(self.config)
        
        # レポーターの初期化
        self.reporter = ObsidianReporter(self.config)
        
        # データベースマネージャーの初期化
        self.db_manager = DatabaseManager(self.db_path)
        
        logger.info("Initialization complete")
    
    def _init_database(self):
        """SQLiteデータベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 価格データテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                date TEXT PRIMARY KEY,
                gold_price REAL,
                silver_price REAL,
                gold_silver_ratio REAL
            )
        ''')
        
        # マクロ指標テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS macro_indicators (
                date TEXT PRIMARY KEY,
                real_rate REAL,
                ism_pmi REAL,
                dollar_index REAL
            )
        ''')
        
        # 分析結果テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                date TEXT PRIMARY KEY,
                fragility_level TEXT,
                fragility_score INTEGER,
                ratio_zscore REAL,
                ratio_percentile REAL,
                analysis_json TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def fetch_historical_data(self, start_date: str = None):
        """過去データの一括取得"""
        if start_date is None:
            start_date = self.config['historical_data']['start_date']
        
        logger.info(f"Fetching historical data from {start_date}...")
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.now()
        
        # 価格データの取得
        try:
            price_data = self.yahoo.fetch(start, end)
            self._save_price_data(price_data)
            logger.info(f"Saved {len(price_data)} price records")
        except DataSourceError as e:
            logger.error(f"Failed to fetch price data: {e}")
            return False
        
        # マクロ指標の取得
        if self.fred:
            try:
                macro_data = self.fred.fetch(start, end)
                self._save_macro_data(macro_data)
                logger.info(f"Saved {len(macro_data)} macro records")
            except DataSourceError as e:
                logger.warning(f"Failed to fetch macro data: {e}")
        
        return True
    
    def update_daily_data(self):
        """日次データ更新"""
        logger.info("Starting daily data update...")
        
        # 直近7日間のデータを取得（欠損対策）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 価格データの更新
        try:
            price_data = self.yahoo.fetch(start_date, end_date)
            self._save_price_data(price_data)
            logger.info(f"Updated {len(price_data)} price records")
        except DataSourceError as e:
            logger.error(f"Failed to update price data: {e}")
            return False
        
        # マクロ指標の更新
        if self.fred:
            try:
                macro_data = self.fred.fetch(start_date, end_date)
                self._save_macro_data(macro_data)
                logger.info(f"Updated {len(macro_data)} macro records")
            except DataSourceError as e:
                logger.warning(f"Failed to update macro data: {e}")
        
        return True
    
    def run_analysis(self):
        """分析の実行"""
        logger.info("Running fragility analysis...")
        
        # データベースから最新データを取得
        conn = sqlite3.connect(self.db_path)
        
        # 価格データ（過去1年分）
        price_data = pd.read_sql_query(
            '''
            SELECT * FROM price_data 
            ORDER BY date DESC 
            LIMIT 300
            ''',
            conn,
            index_col='date',
            parse_dates=['date']
        ).sort_index()
        
        if price_data.empty:
            logger.error("No price data available for analysis")
            conn.close()
            return None
        
        # マクロ指標
        macro_data = None
        try:
            macro_data = pd.read_sql_query(
                '''
                SELECT * FROM macro_indicators 
                ORDER BY date DESC 
                LIMIT 300
                ''',
                conn,
                index_col='date',
                parse_dates=['date']
            ).sort_index()
        except:
            logger.warning("No macro data available")
        
        conn.close()
        
        # 分析実行
        analysis_result = {}
        
        # 金銀比価分析
        ratio_analysis = self.analyzer.analyze_gold_silver_ratio(
            price_data['gold_silver_ratio']
        )
        analysis_result['gold_silver_ratio'] = ratio_analysis
        analysis_result['ratio_fragility'] = ratio_analysis['fragility_level']
        
        # 銀価格モメンタム
        silver_momentum = self.analyzer.analyze_price_momentum(
            price_data['silver_price'],
            name='silver'
        )
        analysis_result['silver_momentum'] = silver_momentum
        
        # 金価格モメンタム
        gold_momentum = self.analyzer.analyze_price_momentum(
            price_data['gold_price'],
            name='gold'
        )
        analysis_result['gold_momentum'] = gold_momentum
        
        # マクロ指標（利用可能な場合）
        if macro_data is not None and not macro_data.empty:
            latest_macro = macro_data.iloc[-1].to_dict()
            analysis_result['macro_indicators'] = latest_macro
        
        # 複合シグナル検知
        composite_signals = self.analyzer.detect_composite_signals(analysis_result)
        analysis_result['composite_signals'] = composite_signals
        
        # 総合脆弱性スコア
        fragility_score = self.analyzer.generate_fragility_score(analysis_result)
        analysis_result['fragility_score'] = fragility_score
        
        # 分析結果を保存
        self._save_analysis_result(analysis_result)
        
        logger.info(f"Analysis complete: Level={ratio_analysis['fragility_level']}, Score={fragility_score}")
        
        return analysis_result
    
    def generate_report(self, analysis_result: dict):
        """レポート生成"""
        logger.info("Generating report...")
        
        # Obsidianレポート生成
        report = self.reporter.generate_daily_report(analysis_result)
        filepath = self.reporter.save_report(report)
        logger.info(f"Report saved to {filepath}")
        
        # サマリーログ
        summary = self.reporter.generate_summary_log(analysis_result)
        logger.info(f"Summary: {summary}")
        
        return filepath
    
    def _save_price_data(self, df: pd.DataFrame):
        """価格データをDBに保存"""
        conn = sqlite3.connect(self.db_path)
        df.to_sql('price_data', conn, if_exists='replace', index=True, index_label='date')
        conn.close()
    
    def _save_macro_data(self, df: pd.DataFrame):
        """マクロ指標をDBに保存"""
        conn = sqlite3.connect(self.db_path)
        df.to_sql('macro_indicators', conn, if_exists='replace', index=True, index_label='date')
        conn.close()
    
    def _save_analysis_result(self, result: dict):
        """分析結果をDBに保存"""
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO analysis_results 
            (date, fragility_level, fragility_score, ratio_zscore, ratio_percentile, analysis_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d'),
            result['ratio_fragility'],
            result['fragility_score'],
            result['gold_silver_ratio']['zscore'],
            result['gold_silver_ratio']['percentile'],
            json.dumps(result, default=str)
        ))
        
        conn.commit()
        conn.close()


def main():
    """メイン実行関数"""
    try:
        monitor = GoldSilverMonitor()
        
        # ログローテーション（10MB超えで実行）
        rotate_logs(log_dir='/data', max_size_mb=10, keep_files=5)
        
        # データベースが空の場合、過去データを取得
        conn = sqlite3.connect(monitor.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM price_data')
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            logger.info("No historical data found, fetching from 1971...")
            monitor.fetch_historical_data()
        else:
            logger.info(f"Found {count} existing records, updating daily data...")
            monitor.update_daily_data()
        
        # 週次メンテナンス（日曜日に実行）
        if datetime.now().weekday() == 6:  # 0=月曜, 6=日曜
            logger.info("Running weekly maintenance...")
            
            # データベース最適化
            monitor.db_manager.optimize_database()
            
            # バックアップ作成（過去7日分保持）
            monitor.db_manager.backup_database(keep_backups=7)
        
        # 月次メンテナンス（毎月1日に実行）
        if datetime.now().day == 1:
            logger.info("Running monthly maintenance...")
            
            # データローテーション（2年以上前のデータをアーカイブ）
            monitor.db_manager.rotate_data(retention_days=730)
            
            # 古いアーカイブの削除（10年以上前）
            monitor.db_manager.cleanup_archives(max_age_days=3650)
            
            # メンテナンスレポート
            report = monitor.db_manager.generate_maintenance_report()
            logger.info(f"\n{report}")
        
        # 分析実行
        analysis_result = monitor.run_analysis()
        
        if analysis_result:
            # レポート生成
            monitor.generate_report(analysis_result)
            
            # データベース情報をログ出力
            db_info = monitor.db_manager.get_database_size()
            logger.info(f"Database size: {db_info['total_mb']}MB, "
                       f"Price records: {db_info['tables']['price_data']}")
            
            logger.info("Daily monitoring cycle complete")
        else:
            logger.error("Analysis failed")
            sys.exit(1)
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
