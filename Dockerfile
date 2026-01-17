# Python 3.11 をベースにした簡単な Dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存パッケージ（必要なら追加）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をコピーしてインストール
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# アプリケーションをコピー
COPY . /app

# 実行スクリプトを実行可能に
RUN chmod +x /app/run.sh

ENV PYTHONUNBUFFERED=1

CMD ["/app/run.sh"]
