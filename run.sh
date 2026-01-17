#!/usr/bin/env bash
set -euo pipefail

# 仮想環境などが不要なシンプルな起動スクリプト
python -m src.main "$@"
