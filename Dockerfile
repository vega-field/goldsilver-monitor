FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY src/ ./src/
COPY config/ ./config/

# データディレクトリの作成
RUN mkdir -p /data

# 定期実行用のエントリーポイント
CMD ["python", "src/main.py"]
