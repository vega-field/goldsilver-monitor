# QUICKSTART (日本語)

このプロジェクトを素早く起動する手順です。

1) リポジトリ作成（例: gh CLI）
```bash
gh repo create vega-field/goldsilver-monitor --public --description "Gold-Silver Market Fragility Monitoring System with Azure AI Foundry Integration" --license mit --gitignore Python --default-branch main --confirm
```

2) ローカルセットアップ
```bash
git clone https://github.com/vega-field/goldsilver-monitor.git
cd goldsilver-monitor
cp .env.example .env
# .env を編集して API キー等を設定
pip install -r requirements.txt
```

3) 設定ファイルを編集
- `config/config.yaml` をプロジェクト要件に合わせて編集します。

4) 実行
```bash
./run.sh
```

5) Docker で実行
```bash
docker-compose up --build
```

補足
- Azure 認証や FRED API キーなどの機密情報は `.env` で管理してください。
- 初期ファイルは最小限のスケルトンです。実運用に合わせてユニットテスト、CI（GitHub Actions）などを追加してください。