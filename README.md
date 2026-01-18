# 金銀市場脆弱性監視システム

ニクソンショック（1971年）以降の金銀比価を監視し、市場構造の脆弱性を検知するシステム。

## 特徴

- **構造的脆弱性の検知**: 価格予測ではなく、ポジション偏り、統計的異常値、急変動などの構造的リスクを監視
- **無料データソース**: Yahoo Finance + FRED APIで完全無料運用
- **軽量コンテナ**: Synology NAS上で省リソース実行
- **Obsidian連携**: 日次レポートをMarkdown形式で自動生成
- **拡張可能設計**: 後からCFTC、ETFフロー等のデータソース追加が容易
- **自動メンテナンス**: データローテーション、バックアップ、最適化を自動実行

## システム構成

```
監視指標:
┌─────────────────────────────────┐
│ コア指標（日次）                │
├─────────────────────────────────┤
│ ✓ 金銀比価 (Yahoo Finance)      │
│ ✓ 実質金利 (FRED)               │
│ ✓ 製造業PMI (FRED)              │
│ ✓ ドルインデックス (Yahoo)      │
└─────────────────────────────────┘

脆弱性分析:
- Z-score分析（統計的異常値検知）
- パーセンタイル計算（歴史的位置）
- モメンタム分析（価格変動率）
- 複合シグナル検知
```

## 必要な準備

### 1. FRED APIキーの取得

1. https://fred.stlouisfed.org/ にアクセス
2. アカウント作成（無料）
3. https://fred.stlouisfed.org/docs/api/api_key.html でAPIキー発行
4. `.env`ファイルに設定

### 2. Synology NAS環境

- DSM 7.0以上
- Container Manager（旧Docker）インストール済み
- 最低メモリ: 512MB
- ストレージ: 初年度数十MB、長期で数GB

## セットアップ手順

### 1. ファイルのアップロード

Synology File Stationで、プロジェクト全体をNASにアップロード（例: `/docker/goldsilver-monitor`）

### 2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集してFRED APIキーを設定
```

### 3. Container Managerでのデプロイ

**方法A: Docker Composeを使用（推奨）**

1. Container Manager → プロジェクト → 作成
2. プロジェクト名: `goldsilver-monitor`
3. パス: `/docker/goldsilver-monitor`
4. docker-compose.ymlを選択
5. 環境変数（.env）を設定
6. 開始

**方法B: 手動でコンテナ作成**

```bash
# SSH接続後
cd /volume1/docker/goldsilver-monitor
docker build -t goldsilver-monitor .
docker run -d \
  --name goldsilver-monitor \
  -v $(pwd)/data:/data \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/reports:/reports \
  -e FRED_API_KEY=your_key_here \
  --restart unless-stopped \
  goldsilver-monitor
```

### 4. 初回実行

初回はニクソンショック以降の過去データ取得に10-20分かかります。

```bash
# ログ確認
docker logs -f goldsilver-monitor
```

## 運用方法

### 日次自動実行

cron風のスケジューリング設定例（docker-compose.ymlで調整）:

```yaml
command: sh -c "while true; do python src/main.py && sleep 86400; done"
```

毎日午前2時実行（市場クローズ後）が推奨。

### 手動実行

```bash
docker exec goldsilver-monitor python src/main.py
```

### レポート確認

生成されたレポートは`/reports`ディレクトリに保存されます:

```
reports/
├── fragility_report_2024-12-13.md
├── fragility_report_2024-12-14.md
└── ...
```

Obsidian vaultに`/reports`ディレクトリをシンボリックリンクすれば、自動的にノートとして参照可能。

## データ構造

### SQLiteデータベース

`/data/market_data.db`に以下のテーブルが作成されます:

- `price_data`: 金銀価格と比価
- `macro_indicators`: マクロ経済指標
- `analysis_results`: 日次分析結果

### レポート形式

Obsidianフロントマター付きMarkdown:

```markdown
---
date: 2024-12-13
type: market-fragility-report
fragility_level: MODERATE
fragility_score: 55
tags: [金銀比価, 市場脆弱性]
---

# 金銀市場脆弱性レポート 🟡
...
```

## カスタマイズ

### 閾値の変更

`config/config.yaml`で調整:

```yaml
fragility_thresholds:
  gold_silver_ratio:
    critical_high: 85  # お好みで変更
    high: 80
```

### 通知の追加

`src/alerts/`に新しいクラスを追加:

```python
class SlackNotifier:
    def send_alert(self, analysis_result):
        # Webhook実装
```

### データソースの追加

`src/data_sources/`に新しいクラスを追加:

```python
class CFTCScraperSource(DataSource):
    # CFTC投機筋ポジションのスクレイピング
```

## トラブルシューティング

### FRED APIエラー

```
DataSourceError: FRED API key is required
```

→ `.env`ファイルでFRED_API_KEYが正しく設定されているか確認

### Yahoo Financeエラー

```
Yahoo Finance data fetch failed
```

→ ネットワーク接続確認。一時的なAPI制限の可能性あり（数分待って再実行）

### メモリ不足

→ docker-compose.ymlでメモリ制限を緩和:

```yaml
deploy:
  resources:
    limits:
      memory: 1G
```

## ロードマップ

### Phase 2（予定）
- [ ] CFTC投機筋ポジションのスクレイピング
- [ ] ETFフロー監視
- [ ] Grafanaダッシュボード
- [ ] Slack/Discord通知

### Phase 3（予定）
- [ ] オプションIV監視
- [ ] 機械学習による異常検知
- [ ] バックテスト機能

## データベース運用

システムは自動メンテナンス機能を備えています：

### 自動メンテナンススケジュール
- **日次**: データ更新、ログローテーション
- **週次**: データベース最適化、バックアップ作成
- **月次**: データローテーション（2年以上前をアーカイブ）、古いアーカイブ削除

### 手動メンテナンス
```bash
# 状態確認
./maintenance.sh info

# バックアップ作成
./maintenance.sh backup

# データローテーション（1年以上前）
./maintenance.sh rotate 365

# 完全メンテナンス
./maintenance.sh full
```

詳細は`DATABASE_OPERATIONS.md`を参照。

### ストレージ見積もり
- 2年分のデータベース: ~120KB
- 10年運用時の総容量: ~100MB未満

**Synology NASへの負荷は極小です**

## ライセンス

MIT License

## 作者

Match - University of Tokyo CARF
