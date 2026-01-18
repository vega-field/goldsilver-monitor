# 金銀市場脆弱性監視システム - プロジェクト概要

## 🎯 プロジェクトの目的

ニクソンショック（1971年）以降の金銀比価を継続的に監視し、市場構造の脆弱性を自動検知するシステム。価格予測ではなく、**構造的リスクの可視化**に焦点を当てた研究用ツール。

## 📊 主な機能

### コア分析
- **金銀比価の統計分析**: Z-score、パーセンタイル、移動平均乖離
- **価格モメンタム監視**: 日次/週次変化率、ボラティリティ
- **複合シグナル検知**: 高比価×価格下落、統計的異常値など
- **脆弱性スコアリング**: 0-100点での総合評価

### データソース（完全無料）
- **Yahoo Finance**: 金銀価格、ドルインデックス
- **FRED API**: 実質金利、製造業PMI等のマクロ指標
- **拡張可能設計**: CFTC、ETFフロー等の後付け追加が容易

### 出力
- **Obsidian連携レポート**: Markdownフォーマットで日次自動生成
- **SQLiteデータベース**: 全履歴データの保存・分析可能
- **構造化ログ**: 機械可読形式でのサマリー出力

## 🏗️ システムアーキテクチャ

```
┌─────────────────────────────────────────┐
│  Synology NAS Container                 │
│  ┌───────────────────────────────────┐  │
│  │ goldsilver-monitor                │  │
│  │                                   │  │
│  │  ┌──────────┐    ┌──────────┐   │  │
│  │  │ Yahoo    │    │ FRED     │   │  │
│  │  │ Finance  │    │ API      │   │  │
│  │  └────┬─────┘    └────┬─────┘   │  │
│  │       │               │          │  │
│  │       v               v          │  │
│  │  ┌─────────────────────────┐    │  │
│  │  │  Fragility Analyzer     │    │  │
│  │  │  - Z-score計算          │    │  │
│  │  │  - モメンタム分析       │    │  │
│  │  │  - シグナル検知         │    │  │
│  │  └──────────┬──────────────┘    │  │
│  │             │                   │  │
│  │             v                   │  │
│  │  ┌─────────────────────────┐    │  │
│  │  │  SQLite Database        │    │  │
│  │  │  - 価格履歴             │    │  │
│  │  │  - マクロ指標           │    │  │
│  │  │  - 分析結果             │    │  │
│  │  └──────────┬──────────────┘    │  │
│  │             │                   │  │
│  │             v                   │  │
│  │  ┌─────────────────────────┐    │  │
│  │  │  Obsidian Reporter      │    │  │
│  │  │  - Markdownレポート     │    │  │
│  │  │  - 構造化ログ           │    │  │
│  │  └──────────┬──────────────┘    │  │
│  └─────────────┼───────────────────┘  │
│                v                      │
│     /reports/ ディレクトリ            │
└───────────────────────────────────────┘
           │
           v
    Obsidian Vault
```

## 📁 ファイル構成

```
goldsilver-monitor/
├── README.md               # プロジェクト概要
├── DEPLOY.md              # デプロイ手順詳細
├── QUICKSTART.md          # このファイル
├── docker-compose.yml     # コンテナ構成
├── Dockerfile            # コンテナイメージ定義
├── requirements.txt      # Pythonパッケージ
├── .env.example          # 環境変数テンプレート
├── run.sh                # 起動スクリプト
├── test.py               # テストスクリプト
│
├── config/
│   └── config.yaml       # 閾値・設定
│
├── src/
│   ├── main.py           # メインプログラム
│   ├── data_sources/     # データ取得
│   │   ├── base.py
│   │   ├── yahoo_finance.py
│   │   └── fred.py
│   ├── analyzers/        # 分析エンジン
│   │   └── fragility.py
│   └── alerts/           # レポート生成
│       └── obsidian.py
│
├── data/                 # SQLiteデータベース（自動生成）
└── reports/              # 日次レポート（自動生成）
```

## ⚡ クイックスタート

### 最小3ステップでデプロイ

```bash
# 1. FRED APIキーを取得（5分）
https://fred.stlouisfed.org/docs/api/api_key.html

# 2. NASにアップロード＆解凍
# goldsilver-monitor.tar.gz → /docker/goldsilver-monitor

# 3. 環境変数を設定して起動
cd /volume1/docker/goldsilver-monitor
cp .env.example .env
nano .env  # FRED_API_KEY=xxx を設定
docker-compose up -d
```

**詳細は`DEPLOY.md`参照**

## 🔧 カスタマイズポイント

### 閾値の変更

`config/config.yaml`:
```yaml
fragility_thresholds:
  gold_silver_ratio:
    critical_high: 85  # あなたの基準に変更
    high: 80
    low: 50
```

### レポート形式

`src/alerts/obsidian.py`の`generate_daily_report()`メソッドを編集

### データソース追加

```python
# src/data_sources/cftc_scraper.py
class CFTCScraperSource(DataSource):
    def fetch(self, start_date, end_date):
        # スクレイピング実装
        pass
```

## 📈 使用例

### 日常的な使い方

1. **朝の確認**: `/reports`フォルダの最新レポートを開く
2. **脆弱性レベル確認**: 🟢(LOW) → 🟡(MODERATE) → 🟠(HIGH) → 🔴(CRITICAL)
3. **シグナル確認**: 検知された複合シグナルをチェック
4. **推奨アクション**: レポート下部の監視項目を確認

### 研究用途

```python
# データベースから過去データを取得
import sqlite3
import pandas as pd

conn = sqlite3.connect('/volume1/docker/goldsilver-monitor/data/market_data.db')
df = pd.read_sql_query('SELECT * FROM price_data', conn, parse_dates=['date'])

# 独自の分析
# ...
```

### アラート設定例

`config/config.yaml`で閾値を調整後、Synologyタスクスケジューラで：

```bash
# 脆弱性スコア70以上でメール送信
docker exec goldsilver-monitor python -c "
import sqlite3
conn = sqlite3.connect('/data/market_data.db')
cursor = conn.cursor()
cursor.execute('SELECT fragility_score FROM analysis_results ORDER BY date DESC LIMIT 1')
score = cursor.fetchone()[0]
if score >= 70:
    print('HIGH FRAGILITY ALERT: Score=' + str(score))
" | mail -s "Market Alert" your@email.com
```

## 🎓 理論的背景

### 脆弱性検知の3層構造

1. **構造的指標**: ポジション偏り、需給バランス
2. **統計的指標**: Z-score、パーセンタイル
3. **動的指標**: モメンタム、ボラティリティ

### 金銀比価の歴史的パターン

- **過去100年平均**: 60-70
- **極端な高値**: 80超え（銀の割安）→ 平均30-60日後に反転傾向
- **極端な安値**: 50未満（銀の割高）→ 調整リスク

### 機関投資家の行動パターン

- **CFTC報告**: 4日遅れだが、極端なポジション偏りは反転の先行指標
- **ETFフロー**: 1-2日遅れ、連続流出/流入は加速度的変化の兆候
- **価格変動**: 流動性が低いため、大口の動きは必然的に価格に現れる

## 🔮 ロードマップ

### Phase 2（開発予定）
- [ ] CFTC投機筋ポジションの週次スクレイピング
- [ ] ETFフロー監視（iShares Silver Trust等）
- [ ] Grafanaダッシュボード構築
- [ ] Slack/Discord Webhook通知

### Phase 3（構想段階）
- [ ] オプション市場のIV監視
- [ ] 機械学習による異常検知（Isolation Forest等）
- [ ] 過去データでのバックテスト機能
- [ ] RESTful API提供

## 📊 リソース使用量

- **CPU**: ほぼアイドル（実行時のみ数分）
- **メモリ**: 256-512MB
- **ストレージ**: 
  - 初年度: 50-100MB
  - 10年運用: 数GB
- **ネットワーク**: 日次数MB

**Synology NASへの負荷は極小です**

## 🤝 貢献・カスタマイズ

このプロジェクトは研究用途を想定しており、自由にカスタマイズ可能です：

- 新しいデータソースの追加
- 独自の脆弱性指標の実装
- 通知システムの拡張
- バックテスト機能の追加

## 📝 ライセンス

MIT License

## 👤 開発者

Match - University of Tokyo, Center for Advanced Research in Finance (CARF)

---

**次のステップ**: `DEPLOY.md`を読んで、実際にSynology NASにデプロイしてみましょう！
