"""
データベース管理ツール
- アーカイブ: 古いデータをCSVに書き出し
- ローテーション: 一定期間以上のデータを削除
- 最適化: VACUUM, ANALYZE実行
- バックアップ: SQLiteファイルのコピー
"""

import sqlite3
import pandas as pd
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = '/data/market_data.db', 
                 archive_dir: str = '/data/archives'):
        self.db_path = db_path
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(exist_ok=True)
        
        # バックアップディレクトリ
        self.backup_dir = Path('/data/backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_database_size(self) -> dict:
        """データベースのサイズ情報を取得"""
        if not os.path.exists(self.db_path):
            return {'total_mb': 0, 'tables': {}}
        
        total_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables_info = {}
        for table in ['price_data', 'macro_indicators', 'analysis_results']:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                tables_info[table] = count
            except:
                tables_info[table] = 0
        
        conn.close()
        
        return {
            'total_mb': round(total_size, 2),
            'tables': tables_info
        }
    
    def archive_old_data(self, table_name: str, cutoff_date: datetime, 
                        compress: bool = True) -> str:
        """
        古いデータをCSVアーカイブに移動
        
        Args:
            table_name: テーブル名
            cutoff_date: この日付より古いデータをアーカイブ
            compress: gzip圧縮するか
            
        Returns:
            アーカイブファイルパス
        """
        logger.info(f"Archiving {table_name} data before {cutoff_date.date()}")
        
        conn = sqlite3.connect(self.db_path)
        
        # アーカイブ対象データを取得
        query = f"""
            SELECT * FROM {table_name}
            WHERE date < ?
            ORDER BY date
        """
        
        df = pd.read_sql_query(query, conn, params=(cutoff_date.strftime('%Y-%m-%d'),))
        
        if df.empty:
            logger.info(f"No data to archive for {table_name}")
            conn.close()
            return None
        
        # アーカイブファイル名
        archive_date = cutoff_date.strftime('%Y-%m-%d')
        filename = f"{table_name}_archive_{archive_date}.csv"
        
        if compress:
            filename += '.gz'
            filepath = self.archive_dir / filename
            # gzip圧縮して保存
            df.to_csv(filepath, index=False, compression='gzip')
        else:
            filepath = self.archive_dir / filename
            df.to_csv(filepath, index=False)
        
        # 元データを削除
        cursor = conn.cursor()
        cursor.execute(f"""
            DELETE FROM {table_name}
            WHERE date < ?
        """, (cutoff_date.strftime('%Y-%m-%d'),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Archived {len(df)} records, deleted {deleted_count} records")
        logger.info(f"Archive saved to {filepath}")
        
        return str(filepath)
    
    def rotate_data(self, retention_days: int = 730):
        """
        データローテーション - デフォルト2年間保持
        
        Args:
            retention_days: 保持日数（デフォルト730日=2年）
        """
        logger.info(f"Starting data rotation (retention: {retention_days} days)")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # 各テーブルをアーカイブ
        for table in ['price_data', 'macro_indicators']:
            try:
                self.archive_old_data(table, cutoff_date, compress=True)
            except Exception as e:
                logger.error(f"Failed to archive {table}: {e}")
        
        # 分析結果は90日（3ヶ月）保持
        analysis_cutoff = datetime.now() - timedelta(days=90)
        try:
            self.archive_old_data('analysis_results', analysis_cutoff, compress=True)
        except Exception as e:
            logger.error(f"Failed to archive analysis_results: {e}")
        
        # 最適化実行
        self.optimize_database()
    
    def optimize_database(self):
        """データベースの最適化（VACUUM, ANALYZE）"""
        logger.info("Optimizing database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # VACUUM: データベースファイルを圧縮
        cursor.execute('VACUUM')
        
        # ANALYZE: クエリオプティマイザの統計情報更新
        cursor.execute('ANALYZE')
        
        conn.commit()
        conn.close()
        
        logger.info("Database optimization complete")
    
    def backup_database(self, keep_backups: int = 7) -> str:
        """
        データベースをバックアップ
        
        Args:
            keep_backups: 保持するバックアップ数
            
        Returns:
            バックアップファイルパス
        """
        if not os.path.exists(self.db_path):
            logger.warning("Database file not found, skipping backup")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"market_data_backup_{timestamp}.db.gz"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"Creating backup: {backup_path}")
        
        # gzip圧縮してバックアップ
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 古いバックアップを削除
        self._cleanup_old_backups(keep_backups)
        
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
        logger.info(f"Backup created: {backup_size:.2f}MB")
        
        return str(backup_path)
    
    def _cleanup_old_backups(self, keep_count: int):
        """古いバックアップを削除"""
        backups = sorted(self.backup_dir.glob('market_data_backup_*.db.gz'))
        
        if len(backups) > keep_count:
            for old_backup in backups[:-keep_count]:
                logger.info(f"Removing old backup: {old_backup}")
                old_backup.unlink()
    
    def restore_from_backup(self, backup_path: str):
        """バックアップから復元"""
        logger.info(f"Restoring from backup: {backup_path}")
        
        # 現在のDBをリネーム
        if os.path.exists(self.db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            old_db = f"{self.db_path}.old_{timestamp}"
            shutil.move(self.db_path, old_db)
            logger.info(f"Current DB moved to: {old_db}")
        
        # バックアップを解凍して復元
        with gzip.open(backup_path, 'rb') as f_in:
            with open(self.db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info("Database restored successfully")
    
    def cleanup_archives(self, max_age_days: int = 3650):
        """
        古いアーカイブファイルを削除
        
        Args:
            max_age_days: アーカイブの最大保持日数（デフォルト10年）
        """
        logger.info(f"Cleaning up archives older than {max_age_days} days")
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        removed_count = 0
        for archive_file in self.archive_dir.glob('*_archive_*.csv*'):
            if archive_file.stat().st_mtime < cutoff_timestamp:
                logger.info(f"Removing old archive: {archive_file}")
                archive_file.unlink()
                removed_count += 1
        
        logger.info(f"Removed {removed_count} old archive files")
    
    def get_archive_summary(self) -> dict:
        """アーカイブの概要を取得"""
        archives = list(self.archive_dir.glob('*_archive_*.csv*'))
        
        summary = {
            'count': len(archives),
            'total_size_mb': 0,
            'files': []
        }
        
        for archive in archives:
            size_mb = archive.stat().st_size / (1024 * 1024)
            summary['total_size_mb'] += size_mb
            summary['files'].append({
                'name': archive.name,
                'size_mb': round(size_mb, 2),
                'date': datetime.fromtimestamp(archive.stat().st_mtime).strftime('%Y-%m-%d')
            })
        
        summary['total_size_mb'] = round(summary['total_size_mb'], 2)
        
        return summary
    
    def generate_maintenance_report(self) -> str:
        """メンテナンスレポートを生成"""
        db_info = self.get_database_size()
        archive_info = self.get_archive_summary()
        
        report = f"""
=== データベースメンテナンスレポート ===
日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【データベース】
- ファイルサイズ: {db_info['total_mb']}MB
- price_data: {db_info['tables'].get('price_data', 0):,} レコード
- macro_indicators: {db_info['tables'].get('macro_indicators', 0):,} レコード
- analysis_results: {db_info['tables'].get('analysis_results', 0):,} レコード

【アーカイブ】
- ファイル数: {archive_info['count']}
- 合計サイズ: {archive_info['total_size_mb']}MB

【バックアップ】
- バックアップ数: {len(list(self.backup_dir.glob('*.db.gz')))}
- 保存先: {self.backup_dir}
"""
        return report


def rotate_logs(log_dir: str = '/data', max_size_mb: int = 10, keep_files: int = 5):
    """
    ログファイルのローテーション
    
    Args:
        log_dir: ログディレクトリ
        max_size_mb: ローテーション閾値（MB）
        keep_files: 保持するログファイル数
    """
    log_file = Path(log_dir) / 'monitor.log'
    
    if not log_file.exists():
        return
    
    # サイズチェック
    size_mb = log_file.stat().st_size / (1024 * 1024)
    
    if size_mb < max_size_mb:
        return
    
    logger.info(f"Rotating log file ({size_mb:.2f}MB)")
    
    # 既存のローテーション済みファイルをシフト
    for i in range(keep_files - 1, 0, -1):
        old_file = Path(log_dir) / f'monitor.log.{i}'
        new_file = Path(log_dir) / f'monitor.log.{i+1}'
        
        if old_file.exists():
            if new_file.exists():
                new_file.unlink()
            old_file.rename(new_file)
    
    # 現在のログファイルをローテーション
    rotated_file = Path(log_dir) / 'monitor.log.1'
    if rotated_file.exists():
        rotated_file.unlink()
    
    # gzip圧縮
    with open(log_file, 'rb') as f_in:
        with gzip.open(str(rotated_file) + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # 元ファイルをクリア
    log_file.unlink()
    log_file.touch()
    
    # 古いログファイルを削除
    for i in range(keep_files + 1, keep_files + 10):
        old_log = Path(log_dir) / f'monitor.log.{i}.gz'
        if old_log.exists():
            old_log.unlink()
    
    logger.info("Log rotation complete")


if __name__ == '__main__':
    # スタンドアロン実行時のテスト
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    manager = DatabaseManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'info':
            print(manager.generate_maintenance_report())
        
        elif command == 'backup':
            manager.backup_database()
        
        elif command == 'rotate':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 730
            manager.rotate_data(retention_days=days)
        
        elif command == 'optimize':
            manager.optimize_database()
        
        elif command == 'cleanup':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 3650
            manager.cleanup_archives(max_age_days=days)
        
        else:
            print("Usage: python db_manager.py [info|backup|rotate|optimize|cleanup]")
    else:
        # デフォルト: 情報表示
        print(manager.generate_maintenance_report())
