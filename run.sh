#!/bin/bash

# 金銀市場監視システム起動スクリプト

set -e

echo "=== Gold-Silver Market Fragility Monitor ==="
echo ""

# 環境変数チェック
if [ -z "$FRED_API_KEY" ]; then
    echo "Error: FRED_API_KEY environment variable is not set"
    echo "Please set it in .env file or export it"
    exit 1
fi

echo "✓ FRED API key configured"
echo ""

# Pythonパッケージチェック
python -c "import yfinance, fredapi, pandas, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: Required Python packages not installed"
    echo "Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
fi

echo "✓ Dependencies installed"
echo ""

# メインプログラム実行
echo "Starting monitoring cycle..."
python src/main.py

echo ""
echo "=== Monitoring cycle complete ==="
