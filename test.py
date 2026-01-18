#!/usr/bin/env python3
"""
簡易テストスクリプト - 主要機能の動作確認
"""

import sys
import os
from datetime import datetime, timedelta

# テスト用の環境変数設定（必要に応じて）
if not os.getenv('FRED_API_KEY'):
    print("Warning: FRED_API_KEY not set. FRED tests will be skipped.")

sys.path.insert(0, '/home/claude/goldsilver-monitor/src')

from data_sources import YahooFinanceSource, FREDSource, DataSourceError


def test_yahoo_finance():
    """Yahoo Financeデータソースのテスト"""
    print("\n=== Testing Yahoo Finance Data Source ===")
    
    try:
        yahoo = YahooFinanceSource({
            'symbols': {'gold': 'GC=F', 'silver': 'SI=F'}
        })
        
        # 最新データ取得
        latest = yahoo.get_latest()
        print(f"✓ Latest data fetched successfully")
        print(f"  Gold: ${latest['gold_price']:.2f}")
        print(f"  Silver: ${latest['silver_price']:.2f}")
        print(f"  Ratio: {latest['gold_silver_ratio']:.2f}")
        print(f"  Date: {latest['date']}")
        
        # 過去1ヶ月のデータ取得
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        df = yahoo.fetch(start_date, end_date)
        print(f"✓ Historical data fetched: {len(df)} records")
        
        return True
        
    except Exception as e:
        print(f"✗ Yahoo Finance test failed: {e}")
        return False


def test_fred():
    """FRED データソースのテスト"""
    print("\n=== Testing FRED Data Source ===")
    
    if not os.getenv('FRED_API_KEY'):
        print("⊘ Skipped: FRED_API_KEY not configured")
        return None
    
    try:
        fred = FREDSource({
            'indicators': {
                'treasury_10y': 'DGS10',
                'breakeven_10y': 'T10YIE',
                'ism_pmi': 'NAPM'
            }
        })
        
        # 最新データ取得
        latest = fred.get_latest()
        print(f"✓ Latest FRED data fetched successfully")
        if 'treasury_10y' in latest:
            print(f"  10Y Treasury: {latest['treasury_10y']:.2f}%")
        if 'real_rate' in latest:
            print(f"  Real Rate: {latest['real_rate']:.2f}%")
        if 'ism_pmi' in latest:
            print(f"  ISM PMI: {latest['ism_pmi']:.1f}")
        
        return True
        
    except Exception as e:
        print(f"✗ FRED test failed: {e}")
        return False


def test_analysis():
    """分析エンジンのテスト"""
    print("\n=== Testing Fragility Analyzer ===")
    
    try:
        from analyzers import FragilityAnalyzer
        import pandas as pd
        import numpy as np
        
        # ダミーデータ生成
        dates = pd.date_range(end=datetime.now(), periods=300, freq='D')
        ratio_data = pd.Series(
            np.random.normal(75, 5, 300),  # 平均75、標準偏差5
            index=dates
        )
        
        analyzer = FragilityAnalyzer({
            'fragility_thresholds': {
                'gold_silver_ratio': {
                    'critical_high': 85,
                    'high': 80,
                    'low': 50,
                    'critical_low': 45
                },
                'zscore': {
                    'extreme': 2.0,
                    'high': 1.5,
                    'moderate': 1.0
                }
            },
            'statistics': {
                'lookback_period': 252,
                'zscore_window': 252
            }
        })
        
        # 分析実行
        result = analyzer.analyze_gold_silver_ratio(ratio_data)
        print(f"✓ Analysis engine working")
        print(f"  Current Ratio: {result['current_value']:.2f}")
        print(f"  Z-score: {result['zscore']:.2f}")
        print(f"  Fragility Level: {result['fragility_level']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reporter():
    """レポーター のテスト"""
    print("\n=== Testing Obsidian Reporter ===")
    
    try:
        from alerts import ObsidianReporter
        
        reporter = ObsidianReporter({
            'reports': {
                'output_dir': '/tmp/test_reports'
            }
        })
        
        # ダミーの分析結果
        dummy_result = {
            'gold_silver_ratio': {
                'current_value': 82.5,
                'zscore': 1.2,
                'percentile': 75.0,
                'ma_20': 80.0,
                'ma_50': 78.0,
                'deviation_from_ma20': 3.1,
                'fragility_level': 'MODERATE',
                'interpretation': 'テスト用データ'
            },
            'silver_momentum': {
                'current_price': 24.50,
                'change_1d_pct': -0.5,
                'change_5d_pct': 2.3,
                'change_20d_pct': -1.2,
                'volatility_20d_annualized': 18.5,
                'is_extreme_daily': False,
                'is_extreme_weekly': False
            },
            'gold_momentum': {
                'current_price': 2020.0,
                'change_1d_pct': 0.3,
                'change_5d_pct': 1.5,
                'change_20d_pct': -0.8
            },
            'ratio_fragility': 'MODERATE',
            'fragility_score': 55,
            'composite_signals': []
        }
        
        # レポート生成
        report = reporter.generate_daily_report(dummy_result)
        print(f"✓ Report generated ({len(report)} chars)")
        
        # サマリーログ
        summary = reporter.generate_summary_log(dummy_result)
        print(f"✓ Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"✗ Reporter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """全テスト実行"""
    print("=" * 50)
    print("Gold-Silver Monitor - Component Tests")
    print("=" * 50)
    
    results = []
    
    # 各テスト実行
    results.append(("Yahoo Finance", test_yahoo_finance()))
    results.append(("FRED API", test_fred()))
    results.append(("Analyzer", test_analysis()))
    results.append(("Reporter", test_reporter()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    for name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r is True)
    total = sum(1 for _, r in results if r is not None)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
