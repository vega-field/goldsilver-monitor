"""
Obsidian vault用のレポート生成
"""

from datetime import datetime
from typing import Dict, Any, List
import os


class ObsidianReporter:
    """Obsidianフォーマットでレポートを生成"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('reports', {}).get('output_dir', '/reports')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_daily_report(self, analysis_result: Dict[str, Any]) -> str:
        """日次レポートを生成"""
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 脆弱性レベルに応じた絵文字
        level_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MODERATE': '🟡',
            'LOW': '🟢'
        }
        
        fragility_level = analysis_result.get('ratio_fragility', 'LOW')
        emoji = level_emoji.get(fragility_level, '⚪')
        
        # レポート本文
        report = f"""---
date: {date_str}
type: market-fragility-report
fragility_level: {fragility_level}
fragility_score: {analysis_result.get('fragility_score', 0)}
tags: [金銀比価, 市場脆弱性, 自動生成]
---

# 金銀市場脆弱性レポート {emoji}

**生成日時**: {timestamp}  
**脆弱性レベル**: {fragility_level}  
**総合スコア**: {analysis_result.get('fragility_score', 0)}/100

---

## 主要指標

### 金銀比価
- **現在値**: {analysis_result['gold_silver_ratio']['current_value']:.2f}
- **Z-score**: {analysis_result['gold_silver_ratio']['zscore']:.2f}
- **パーセンタイル**: {analysis_result['gold_silver_ratio']['percentile']:.1f}%
- **20日移動平均**: {analysis_result['gold_silver_ratio']['ma_20']:.2f}
- **50日移動平均**: {analysis_result['gold_silver_ratio']['ma_50']:.2f}
- **MA20からの乖離**: {analysis_result['gold_silver_ratio']['deviation_from_ma20']:.2f}%

**解釈**: {analysis_result['gold_silver_ratio']['interpretation']}

### 銀価格モメンタム
- **現在価格**: ${analysis_result['silver_momentum']['current_price']:.2f}
- **日次変化**: {analysis_result['silver_momentum']['change_1d_pct']:+.2f}%
- **5日変化**: {analysis_result['silver_momentum']['change_5d_pct']:+.2f}%
- **20日変化**: {analysis_result['silver_momentum']['change_20d_pct']:+.2f}%
- **年率ボラティリティ**: {analysis_result['silver_momentum']['volatility_20d_annualized']:.1f}%

### 金価格モメンタム
- **現在価格**: ${analysis_result['gold_momentum']['current_price']:.2f}
- **日次変化**: {analysis_result['gold_momentum']['change_1d_pct']:+.2f}%
- **5日変化**: {analysis_result['gold_momentum']['change_5d_pct']:+.2f}%

"""
        
        # マクロ指標（利用可能な場合）
        if 'macro_indicators' in analysis_result:
            macro = analysis_result['macro_indicators']
            report += f"""### マクロ経済指標
- **実質金利**: {macro.get('real_rate', 'N/A'):.2f}%
- **製造業PMI**: {macro.get('ism_pmi', 'N/A'):.1f}
"""
        
        # 複合シグナル
        signals = analysis_result.get('composite_signals', [])
        if signals:
            report += "\n---\n\n## 🚨 検知されたシグナル\n\n"
            for signal in signals:
                severity_emoji = level_emoji.get(signal.get('severity', 'LOW'), '⚪')
                report += f"- {severity_emoji} **{signal['type']}**: {signal['message']}\n"
        
        # 推奨監視項目
        report += "\n---\n\n## 📊 推奨監視項目\n\n"
        report += self._generate_recommendations(analysis_result)
        
        # 過去データへのリンク（Obsidianバックリンク）
        report += f"\n---\n\n## 関連ノート\n\n"
        report += f"- [[金銀比価分析 {datetime.now().year}]]\n"
        report += f"- [[市場脆弱性ダッシュボード]]\n"
        
        return report
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> str:
        """推奨監視項目を生成"""
        recommendations = []
        
        ratio = analysis_result['gold_silver_ratio']['current_value']
        zscore = analysis_result['gold_silver_ratio']['zscore']
        
        if ratio > 80:
            recommendations.append("- 金銀比価が80超えで継続中 → 過去データでは平均30-60日後に反転傾向")
            recommendations.append("- ETFフローの反転兆候を監視（Silver Trust流出継続か）")
        
        if ratio < 55:
            recommendations.append("- 低比価圏での過熱感を注意 → 調整リスク")
        
        if abs(zscore) > 1.5:
            recommendations.append(f"- 統計的異常値（Z-score: {zscore:.2f}）→ 平均回帰の可能性")
        
        if analysis_result['silver_momentum']['is_extreme_weekly']:
            recommendations.append("- 銀価格の急変動を検知 → ボラティリティ上昇局面")
        
        # 次回データ更新
        recommendations.append("- 次回CFTC報告（火曜夜）で投機筋ポジション確認")
        
        return "\n".join(recommendations) if recommendations else "- 現時点で特記事項なし"
    
    def save_report(self, report: str, filename: str = None) -> str:
        """レポートをファイルに保存"""
        if filename is None:
            filename = f"fragility_report_{datetime.now().strftime('%Y-%m-%d')}.md"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filepath
    
    def generate_summary_log(self, analysis_result: Dict[str, Any]) -> str:
        """簡易ログ形式のサマリー"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ratio = analysis_result['gold_silver_ratio']['current_value']
        level = analysis_result.get('ratio_fragility', 'LOW')
        score = analysis_result.get('fragility_score', 0)
        
        return (f"[{timestamp}] "
                f"Ratio={ratio:.2f} | "
                f"Level={level} | "
                f"Score={score}/100 | "
                f"Ag={analysis_result['silver_momentum']['change_1d_pct']:+.2f}%")
