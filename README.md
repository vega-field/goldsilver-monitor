# 金銀市場脆弱性監視システム (Gold-Silver Vulnerability Monitor)

ニクソンショック（1971年）以降の金銀比価を監視し、市場構造の脆弱性を検知するシステム。

## 特徴

- **構造的脆弱性の検知**: 価格予測ではなく、ポジション偏り、統計的異常値、急変動などの構造的リスクを監視
- **無料データソース**: Yahoo Finance + FRED APIで完全無料運用
- **軽量コンテナ**: Synology NAS上で省リソース実行
- **Obsidian連携**: 日次レポートをMarkdown形式で自動生成
- **拡張可能設計**: 後からCFTC、ETFフロー等のデータソース追加が容易
- **自動メンテナンス**: データローテーション、バックアップ、最適化を自動実行
- **Azure AI Foundry統合**: Azure OpenAI Serviceを活用した高度な分析機能（オプション）

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

## Azure AI Foundry統合（オプション）

本システムは、Azure AI Foundryとの統合により、以下の高度な分析機能を提供できます：

### 統合機能

1. **自然言語レポート生成**
   - 分析結果を平易な日本語で解説
   - 市場状況の文脈的解釈
   - 投資家向けインサイト生成

2. **高度なパターン認識**
   - GPT-4を活用した複雑な市場パターンの識別
   - 過去の類似局面の自動検索
   - 因果関係の推論

3. **リスクシナリオ生成**
   - 現在の脆弱性から想定されるシナリオ
   - 確率的リスク評価
   - ストレステスト

### セットアップ（Azure統合版）

```yaml
# config/config.yaml に追加
azure_ai:
  enabled: true
  endpoint: https://your-resource.openai.azure.com/
  api_key: ${AZURE_OPENAI_API_KEY}
  deployment_name: gpt-4
  api_version: "2024-02-15-preview"
```

```bash
# 環境変数に追加
echo "AZURE_OPENAI_API_KEY=your_key_here" >> .env
```

**注意**: Azure AI Foundry統合は有料オプションです。基本的な脆弱性監視機能は無料のデータソースのみで動作します。

## 必要な準備

### 1. FRED APIキーの取得（必須・無料）

1. https://fred.stlouisfed.org/ にアクセス
2. アカウント作成（無料）
3. https://fred.stlouisfed.org/docs/api/api_key.html でAPIキー発行
4. `.env`ファイルに設定

### 2. Synology NAS環境

- DSM 7.0以上
- Container Manager（旧Docker）インストール済み
- 最低メモリ: 512MB
- ストレージ: 初年度数十MB、長期で数GB

### 3. Azure AI Foundry（オプション・有料）

- Azure サブスクリプション
- Azure OpenAI Service リソース
- GPT-4デプロイメント

## セットアップ手順

### 基本セットアップ

詳細は `DEPLOY.md` を参照してください。

```bash
# 1. リポジトリをクローン
git clone https://github.com/vega-field/goldsilver-monitor.git
cd goldsilver-monitor

# 2. 環境変数を設定
cp .env.example .env
nano .env  # FRED_API_KEYを設定

# 3. Docker Composeで起動
docker-compose up -d --build

# 4. ログ確認
docker-compose logs -f
```

### Synology NAS へのデプロイ

Container Manager を使用した詳細な手順は `DEPLOY.md` を参照してください。

## 運用方法

### 日次自動実行

デフォルトで以下のスケジュールで自動実行されます：

- **日次**: データ更新、レポート生成、ログローテーション
- **週次**: データベース最適化、バックアップ作成（日曜日）
- **月次**: データローテーション、アーカイブクリーンアップ（毎月1日）

### 手動実行

```bash
# 分析の即座実行
docker exec goldsilver-monitor python src/main.py

# データベース情報確認
./maintenance.sh info

# バックアップ作成
./maintenance.sh backup

# 完全メンテナンス
./maintenance.sh full
```

### レポート確認

生成されたレポートは`/reports`ディレクトリに保存されます:

```
reports/
├── fragility_report_2024-12-15.md
├── fragility_report_2024-12-16.md
└── ...
```

Obsidian vaultに`/reports`ディレクトリをシンボリックリンクすれば、自動的にノートとして参照可能。

## カスタマイズ

### 閾値の変更

`config/config.yaml`:
```yaml
fragility_thresholds:
  gold_silver_ratio:
    critical_high: 85  # あなたの基準に変更
    high: 80
    low: 50
```

### データソース追加

```python
# src/data_sources/cftc_scraper.py
class CFTCScraperSource(DataSource):
    def fetch(self, start_date, end_date):
        # スクレイピング実装
        pass
```

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

## トラブルシューティング

### Q: "FRED API key is required"エラー

A: `.env`ファイルが正しく設定されているか確認
```bash
cat .env
# FRED_API_KEY=... が表示されるべき

# コンテナ再起動
docker-compose down
docker-compose up -d
```

### Q: "Yahoo Finance data fetch failed"

A: ネットワーク接続確認。一時的なAPI制限の可能性あり（数分待って再実行）

### Q: メモリ不足エラー

A: `docker-compose.yml`でメモリ制限を調整:

```yaml
deploy:
  resources:
    limits:
      memory: 1G  # 512M → 1Gに増加
```

## ロードマップ

### Phase 1（現在）✅
- [x] SQLiteベースのデータ蓄積
- [x] 基本的な脆弱性分析
- [x] Obsidianレポート生成
- [x] 自動メンテナンス機能

### Phase 2（計画中）
- [ ] PostgreSQL + Grafana統合
- [ ] CFTC投機筋ポジションのスクレイピング
- [ ] ETFフロー監視
- [ ] リアルタイムダッシュボード

### Phase 3（構想段階）
- [ ] オプションIV監視
- [ ] 機械学習による異常検知
- [ ] バックテスト機能
- [ ] Azure AI Foundryの完全統合

## アーキテクチャ

### Phase 1: SQLite単体（現在）
```
goldsilver-monitor コンテナ
├─ Python アプリ
├─ SQLite (/data/market_data.db)
└─ Obsidian Reports (/reports/)
```

### Phase 2: PostgreSQL + Grafana（計画中）
```
monitor コンテナ → postgres コンテナ → grafana コンテナ
                    └─ 永続化データ    └─ ダッシュボード
```

## ライセンス

MIT License

## 開発者

Match - University of Tokyo, Center for Advanced Research in Finance (CARF)

## 参考資料

- [QUICKSTART.md](QUICKSTART.md) - クイックスタートガイド
- [DEPLOY.md](DEPLOY.md) - 詳細なデプロイ手順
- [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) - データベース運用ガイド

## 貢献

Issue、Pull Requestを歓迎します。新しいデータソースの追加、分析手法の提案など、お気軽にご提案ください。
