# Synology NASへのデプロイ手順

## 前提条件

- Synology NAS (DSM 7.0以上)
- Container Managerがインストール済み
- SSH接続が有効（任意、推奨）
- 最低512MBのメモリ空き容量

## 手順

### 1. FRED APIキーの取得

1. https://fred.stlouisfed.org/ にアクセス
2. 右上の「Sign In」から新規アカウント作成（無料）
3. ログイン後、https://fred.stlouisfed.org/docs/api/api_key.html にアクセス
4. 「Request API Key」をクリック
5. 必要事項を記入（研究目的でOK）
6. APIキーが即座に発行される（例: `abc123def456...`）
7. **このキーをメモしておく**（後で使用）

### 2. ファイルのアップロード

#### 方法A: File Station経由（GUI）

1. Synology File Stationを開く
2. `/docker`フォルダを作成（なければ）
3. `goldsilver-monitor.tar.gz`をアップロード
4. File Stationで右クリック → 「展開」
5. `/docker/goldsilver-monitor`が作成される

#### 方法B: SSH経由

```bash
# ローカルPCから
scp goldsilver-monitor.tar.gz admin@your-nas-ip:/volume1/docker/

# NASにSSH接続
ssh admin@your-nas-ip
cd /volume1/docker
tar -xzf goldsilver-monitor.tar.gz
```

### 3. 環境変数の設定

```bash
cd /volume1/docker/goldsilver-monitor
cp .env.example .env
nano .env  # または vi, vim
```

`.env`ファイルを編集:
```
FRED_API_KEY=ここにあなたのAPIキーを貼り付け
TZ=Asia/Tokyo
```

保存して終了（nanoなら Ctrl+X → Y → Enter）

### 4. Container Managerでのデプロイ

#### GUIからのデプロイ

1. **Container Manager**アプリを開く
2. 左メニューから**プロジェクト**を選択
3. **作成**ボタンをクリック

4. プロジェクト設定:
   - プロジェクト名: `goldsilver-monitor`
   - パス: `docker/goldsilver-monitor` を選択
   - ソース: `docker-compose.yml`を選択

5. **環境**タブ:
   - `FRED_API_KEY`: （手順1で取得したキー）
   - `TZ`: `Asia/Tokyo`

6. **構築**をクリック（初回は5-10分かかる）

7. 構築完了後、**開始**ボタンで起動

#### コマンドラインからのデプロイ（SSH経由）

```bash
cd /volume1/docker/goldsilver-monitor

# .envファイルを確認
cat .env

# Docker Composeで起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

### 5. 初回実行の確認

初回実行では1971年からの過去データを取得するため、**10-20分**かかります。

```bash
# ログをリアルタイムで確認
docker logs -f goldsilver-monitor

# または Container Managerのログビューアで確認
```

以下のようなログが表示されれば成功:
```
INFO - Initializing Gold-Silver Monitor...
INFO - No historical data found, fetching from 1971...
INFO - Saved 13000+ price records
INFO - Analysis complete: Level=MODERATE, Score=55
INFO - Report saved to /reports/fragility_report_2024-12-13.md
```

### 6. レポートの確認

#### 方法A: File Station

1. `/docker/goldsilver-monitor/reports`フォルダを開く
2. `fragility_report_YYYY-MM-DD.md`ファイルを確認

#### 方法B: Obsidian連携

```bash
# Obsidian vaultのディレクトリにシンボリックリンク
ln -s /volume1/docker/goldsilver-monitor/reports /volume1/your-obsidian-vault/Market-Reports
```

Obsidianを再起動すると、`Market-Reports`フォルダにレポートが自動で表示されます。

### 7. 日次自動実行の設定

#### 方法A: Docker内蔵のループ実行（推奨）

`docker-compose.yml`を編集:

```yaml
services:
  monitor:
    # ... 他の設定 ...
    command: sh -c "while true; do python src/main.py && sleep 86400; done"
```

再起動:
```bash
docker-compose down
docker-compose up -d
```

毎日同じ時刻（コンテナ起動時刻）に実行されます。

#### 方法B: Synology タスクスケジューラ

1. **コントロールパネル** → **タスクスケジューラ**
2. **作成** → **予約タスク** → **ユーザー指定のスクリプト**
3. 一般設定:
   - タスク名: `金銀監視 日次実行`
   - ユーザー: `root`
4. スケジュール:
   - 毎日 午前2時（市場クローズ後）
5. タスク設定:
   ```bash
   docker exec goldsilver-monitor python src/main.py
   ```

## トラブルシューティング

### Q: "FRED API key is required"エラー

A: `.env`ファイルが正しく設定されているか確認
```bash
cd /volume1/docker/goldsilver-monitor
cat .env
# FRED_API_KEY=... が表示されるべき

# コンテナ再起動
docker-compose down
docker-compose up -d
```

### Q: "Yahoo Finance data fetch failed"

A: ネットワーク接続を確認。一時的なAPI制限の可能性もあり（数分待って再実行）

```bash
# コンテナからインターネット接続確認
docker exec goldsilver-monitor ping -c 3 8.8.8.8
```

### Q: メモリ不足エラー

A: `docker-compose.yml`でメモリ制限を調整:

```yaml
services:
  monitor:
    # ... 他の設定 ...
    deploy:
      resources:
        limits:
          memory: 1G  # 512M → 1Gに増加
```

### Q: データが更新されない

A: ログを確認して原因特定:

```bash
# 直近100行のログ
docker logs --tail 100 goldsilver-monitor

# エラーメッセージを探す
docker logs goldsilver-monitor 2>&1 | grep -i error
```

### Q: 過去データを再取得したい

A: データベースを削除して再実行:

```bash
docker exec goldsilver-monitor rm /data/market_data.db
docker exec goldsilver-monitor python src/main.py
```

## 動作確認

```bash
# テストスクリプト実行
docker exec goldsilver-monitor python test.py

# 手動で分析実行
docker exec goldsilver-monitor python src/main.py

# レポート確認
ls -lh /volume1/docker/goldsilver-monitor/reports/
```

## アンインストール

```bash
cd /volume1/docker/goldsilver-monitor
docker-compose down
cd ..
rm -rf goldsilver-monitor
```

Container Managerから削除する場合:
1. プロジェクト選択 → **停止**
2. **削除**（コンテナとイメージを削除）

## 次のステップ

- CFTC投機筋ポジションのスクレイピング追加
- Grafanaダッシュボード構築
- Slack/Discord通知設定
- バックテスト機能の実装

## サポート

問題が発生した場合は、以下を確認:
1. `docker logs goldsilver-monitor` の全ログ
2. `/volume1/docker/goldsilver-monitor/data/monitor.log`
3. `.env`ファイルの設定内容（APIキーは伏せて）
