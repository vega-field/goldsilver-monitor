# データベース運用ガイド

## 概要

金銀市場監視システムは、長期運用を前提とした自動メンテナンス機能を備えています。

## 自動メンテナンススケジュール

### 日次（毎日実行）
- データ更新
- ログローテーション（10MB超過時）
- レポート生成

### 週次（日曜日）
- データベース最適化（VACUUM, ANALYZE）
- バックアップ作成（過去7日分保持）

### 月次（毎月1日）
- データローテーション（2年以上前をアーカイブ）
- アーカイブクリーンアップ（10年以上前を削除）
- メンテナンスレポート生成

## データ保持ポリシー

### SQLiteデータベース（高速アクセス用）
```
price_data:          最新2年分
macro_indicators:    最新2年分
analysis_results:    最新3ヶ月分
```

### アーカイブ（長期保存用）
```
場所: /data/archives/
形式: CSV.gz (gzip圧縮)
保持期間: 10年
```

### バックアップ
```
場所: /data/backups/
形式: SQLite.gz (gzip圧縮)
保持数: 過去7日分
```

## ファイルサイズ見積もり

### データベース（2年分）
- price_data: 約500レコード → 50KB
- macro_indicators: 約500レコード → 50KB
- analysis_results: 約90レコード → 20KB
- **合計: 約120KB**（圧縮後: 約30KB）

### アーカイブ（10年分）
- 年間約5MB（CSV.gz）
- 10年で約50MB

### バックアップ（7日分）
- 1ファイル約30KB
- 7ファイルで約210KB

### ログ（5世代）
- 1ファイル10MB
- 5ファイルで約50MB（gzip圧縮後: 約5MB）

**長期運用時の総容量見積もり: 約100-200MB**

## 手動メンテナンス

### 情報確認
```bash
# Dockerコンテナ内で実行
docker exec goldsilver-monitor python src/db_manager.py info

# または
./maintenance.sh info
```

出力例:
```
=== データベースメンテナンスレポート ===
【データベース】
- ファイルサイズ: 0.12MB
- price_data: 500 レコード
- macro_indicators: 500 レコード
- analysis_results: 90 レコード

【アーカイブ】
- ファイル数: 8
- 合計サイズ: 45.2MB
```

### バックアップ作成
```bash
docker exec goldsilver-monitor python src/db_manager.py backup

# または
./maintenance.sh backup
```

### データローテーション
```bash
# 2年以上前をアーカイブ（デフォルト）
docker exec goldsilver-monitor python src/db_manager.py rotate

# 1年以上前をアーカイブ
docker exec goldsilver-monitor python src/db_manager.py rotate 365

# または
./maintenance.sh rotate 365
```

### データベース最適化
```bash
docker exec goldsilver-monitor python src/db_manager.py optimize

# または
./maintenance.sh optimize
```

### アーカイブクリーンアップ
```bash
# 10年以上前を削除（デフォルト）
docker exec goldsilver-monitor python src/db_manager.py cleanup

# 5年以上前を削除
docker exec goldsilver-monitor python src/db_manager.py cleanup 1825

# または
./maintenance.sh cleanup 1825
```

### 完全メンテナンス
```bash
# backup + rotate + optimize + cleanup を一括実行
./maintenance.sh full
```

## バックアップからの復元

### 1. 利用可能なバックアップを確認
```bash
docker exec goldsilver-monitor ls -lh /data/backups/
```

### 2. 復元実行
```python
from db_manager import DatabaseManager

manager = DatabaseManager()
manager.restore_from_backup('/data/backups/market_data_backup_20241213_120000.db.gz')
```

**注意**: 復元前に現在のデータベースは自動的にリネームされます。

## アーカイブの活用

### アーカイブからデータ読み込み
```python
import pandas as pd
import gzip

# gzip圧縮されたCSVを読み込み
df = pd.read_csv('/data/archives/price_data_archive_2020-01-01.csv.gz', compression='gzip')

# 分析に使用
print(df.describe())
```

### 過去データの再インポート
```python
import sqlite3
import pandas as pd

# アーカイブから読み込み
df = pd.read_csv('/data/archives/price_data_archive_2020-01-01.csv.gz', compression='gzip')

# データベースに戻す
conn = sqlite3.connect('/data/market_data.db')
df.to_sql('price_data', conn, if_exists='append', index=False)
conn.close()
```

## トラブルシューティング

### Q: データベースが肥大化した
A: 手動で最適化を実行
```bash
./maintenance.sh optimize
```

### Q: ディスク容量が不足
A: 古いアーカイブとバックアップを削除
```bash
# 5年以上前のアーカイブを削除
./maintenance.sh cleanup 1825

# 古いバックアップを手動削除
docker exec goldsilver-monitor rm /data/backups/market_data_backup_2023*.db.gz
```

### Q: データベースが破損した
A: 最新のバックアップから復元
```bash
# 1. バックアップ一覧確認
docker exec goldsilver-monitor ls -lh /data/backups/

# 2. Pythonスクリプトで復元
docker exec -it goldsilver-monitor python
>>> from db_manager import DatabaseManager
>>> manager = DatabaseManager()
>>> manager.restore_from_backup('/data/backups/market_data_backup_YYYYMMDD_HHMMSS.db.gz')
```

### Q: 過去データを完全に削除したい
A: データベースとアーカイブを削除して再初期化
```bash
docker exec goldsilver-monitor rm /data/market_data.db
docker exec goldsilver-monitor rm -rf /data/archives/*
docker exec goldsilver-monitor rm -rf /data/backups/*

# 再度データ取得（1971年から）
docker exec goldsilver-monitor python src/main.py
```

## 推奨運用パターン

### 通常運用（デフォルト設定）
- 日次: 自動実行
- 週次: 自動バックアップ＋最適化
- 月次: 自動ローテーション＋クリーンアップ
- **→ 設定変更不要、完全自動**

### 省ストレージ運用
`config/config.yaml`を編集:
```yaml
database_management:
  rotation:
    retention_days: 365  # 1年保持
  backup:
    keep_backups: 3  # 3日分
  archive_cleanup:
    max_age_days: 1825  # 5年で削除
```

### 研究用途（全データ保持）
```yaml
database_management:
  rotation:
    enabled: false  # ローテーション無効
  archive_cleanup:
    enabled: false  # クリーンアップ無効
```

### 定期的な確認コマンド

月次で以下を実行推奨:
```bash
# 1. 状態確認
./maintenance.sh info

# 2. 手動バックアップ（重要なデータ変更前）
./maintenance.sh backup

# 3. ディスク使用量確認
docker exec goldsilver-monitor du -sh /data/*
```

## モニタリング

### Synology DSMでの確認
1. **Container Manager** → `goldsilver-monitor`
2. **ログ**タブでメンテナンスログ確認
3. `Running weekly maintenance...` 等のメッセージを確認

### ログファイルでの確認
```bash
# メンテナンスログのgrep
docker exec goldsilver-monitor grep "maintenance" /data/monitor.log

# データベースサイズの推移
docker exec goldsilver-monitor grep "Database size" /data/monitor.log
```

## ベストプラクティス

1. **月次確認**: 毎月1日の自動メンテナンス後、ログを確認
2. **定期バックアップ**: 重要な分析前に手動バックアップ
3. **容量監視**: 半年に1回、ディスク使用量を確認
4. **アーカイブ保存**: 研究用に重要なアーカイブは別途保存
5. **設定調整**: 運用パターンに応じて保持期間を調整

## 参考：ストレージ容量計算

10年間の運用での容量見積もり:

```
データベース（2年分）:        0.12 MB
アーカイブ（8年分）:          40 MB
バックアップ（7日分）:        0.21 MB
ログ（5世代）:               5 MB
レポート（3650ファイル）:     10 MB
──────────────────────────────────
合計:                        55.33 MB
```

**結論**: 10年運用でも100MB未満、Synology NASには全く負荷なし
