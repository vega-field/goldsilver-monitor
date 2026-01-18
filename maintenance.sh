#!/bin/bash

# データベースメンテナンススクリプト
# 手動でメンテナンスを実行する場合に使用

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_MANAGER="python $SCRIPT_DIR/src/db_manager.py"

show_help() {
    cat << EOF
データベースメンテナンススクリプト

使い方:
  ./maintenance.sh <command> [options]

コマンド:
  info              データベースとアーカイブの情報表示
  backup            データベースのバックアップ作成
  rotate [days]     データローテーション (デフォルト: 730日=2年)
  optimize          データベース最適化 (VACUUM, ANALYZE)
  cleanup [days]    古いアーカイブを削除 (デフォルト: 3650日=10年)
  full              完全メンテナンス (backup + rotate + optimize + cleanup)

例:
  ./maintenance.sh info
  ./maintenance.sh backup
  ./maintenance.sh rotate 365    # 1年以上前をアーカイブ
  ./maintenance.sh cleanup 1825  # 5年以上前のアーカイブを削除
  ./maintenance.sh full

EOF
}

case "${1:-}" in
    info)
        echo "=== データベース情報 ==="
        $DB_MANAGER info
        ;;
    
    backup)
        echo "=== バックアップ作成 ==="
        $DB_MANAGER backup
        echo "完了"
        ;;
    
    rotate)
        DAYS=${2:-730}
        echo "=== データローテーション (${DAYS}日保持) ==="
        $DB_MANAGER rotate $DAYS
        echo "完了"
        ;;
    
    optimize)
        echo "=== データベース最適化 ==="
        $DB_MANAGER optimize
        echo "完了"
        ;;
    
    cleanup)
        DAYS=${2:-3650}
        echo "=== アーカイブクリーンアップ (${DAYS}日以上前を削除) ==="
        $DB_MANAGER cleanup $DAYS
        echo "完了"
        ;;
    
    full)
        echo "=== 完全メンテナンス開始 ==="
        echo ""
        
        echo "1/4 バックアップ作成中..."
        $DB_MANAGER backup
        echo ""
        
        echo "2/4 データローテーション中..."
        $DB_MANAGER rotate 730
        echo ""
        
        echo "3/4 データベース最適化中..."
        $DB_MANAGER optimize
        echo ""
        
        echo "4/4 アーカイブクリーンアップ中..."
        $DB_MANAGER cleanup 3650
        echo ""
        
        echo "=== 完全メンテナンス完了 ==="
        $DB_MANAGER info
        ;;
    
    *)
        show_help
        exit 1
        ;;
esac
