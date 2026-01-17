# goldsilver-monitor

Gold-Silver Market Fragility Monitoring System with Azure AI Foundry Integration

概要
- 金（Gold）と銀（Silver）の市場の「fragility（脆弱性／不安定度）」を監視・解析するため���ツール群です。
- データ取得: Yahoo Finance（先物など）、FRED（経済指標）等
- 解析: 価格比率、移動平均、ボラティリティ指標から脆弱性スコアを算出
- アラート: Obsidian へのメモ保存等で可視化／記録

主なフォルダ構成
- config/: 設定ファイル（config.yaml）
- src/: ソースコード
- Dockerfile, docker-compose.yml: コンテナ化設定

セットアップ（簡易）
1. 環境変数を `.env` にコピーして編集（`.env.example` を参照）
2. 依存関係をインストール:
   - ローカル: `pip install -r requirements.txt`
   - Docker: `docker build -t goldsilver-monitor .`
3. 実行: `./run.sh`

ライセンス
- MIT
