#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版报告生成器 - 直接读取MLflow artifacts
"""

import pickle
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def load_pkl(file_path):
    """加载pkl文件"""
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def generate_report():
    """生成报告"""
    # 定位artifacts目录
    mlruns_dir = Path(__file__).parent / "mlruns"
    exp_id = "729227278726044682"
    recorder_id = "5213f1bd7001492f8b44d8225818b602"
    artifacts_dir = mlruns_dir / exp_id / recorder_id / "artifacts"

    print(f"从目录加载数据: {artifacts_dir}")

    # 加载回测结果
    port_analysis = load_pkl(artifacts_dir / "portfolio_analysis" / "port_analysis_1day.pkl")
    indicator_analysis = load_pkl(artifacts_dir / "portfolio_analysis" / "indicator_analysis_1day.pkl")
    report_normal = load_pkl(artifacts_dir / "portfolio_analysis" / "report_normal_1day.pkl")

    # 创建输出目录
    output_dir = Path(__file__).parent.parent / "agent-docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成Markdown报告
    report_path = output_dir / "backtest_report.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        # 标题和概述
        f.write("# 加密货币量化交易回测报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 1. 项目概述\n\n")
        f.write("本项目使用 Qlib 量化投资平台对 ETH/USDT 和 BTC/USDT 两种加密货币现货进行行情分析和回测。\n\n")
        f.write("### 1.1 配置参数\n\n")
        f.write("- **数据来源**: Gate.io 交易所 API\n")
        f.write("- **数据时间范围**: 2024-01-01 至 2025-10-12\n")
        f.write("- **交易对**: ETH/USDT, BTC/USDT\n")
        f.write("- **数据频率**: 日线（1d）\n")
        f.write("- **模型**: LightGBM\n")
        f.write("- **特征集**: Alpha158（158个技术指标特征）\n")
        f.write("- **训练集**: 2024-01-01 至 2024-08-31\n")
        f.write("- **验证集**: 2024-09-01 至 2024-11-30\n")
        f.write("- **测试集**: 2024-12-01 至 2025-10-10\n\n")

        # 数据统计
        f.write("## 2. 数据统计\n\n")
        f.write("| 交易对 | 数据条数 | 开始日期 | 结束日期 |\n")
        f.write("| --- | --- | --- | --- |\n")
        f.write("| BTC/USDT | 651 | 2024-01-01 | 2025-10-12 |\n")
        f.write("| ETH/USDT | 651 | 2024-01-01 | 2025-10-12 |\n\n")

        # 回测性能指标
        f.write("## 3. 回测性能指标\n\n")

        # 基准收益
        f.write("### 3.1 基准收益（Benchmark - BTC/USDT）\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("| --- | --- |\n")

        if 'bench' in port_analysis:
            bench = port_analysis['bench']
            mean_val = bench.get('mean', bench['risk'].get('mean', 0)) if isinstance(bench, dict) else bench.loc['mean', 'risk']
            std_val = bench.get('std', bench['risk'].get('std', 0)) if isinstance(bench, dict) else bench.loc['std', 'risk']
            ann_ret = bench.get('annualized_return', bench['risk'].get('annualized_return', 0)) if isinstance(bench, dict) else bench.loc['annualized_return', 'risk']
            ir = bench.get('information_ratio', bench['risk'].get('information_ratio', 0)) if isinstance(bench, dict) else bench.loc['information_ratio', 'risk']
            max_dd = bench.get('max_drawdown', bench['risk'].get('max_drawdown', 0)) if isinstance(bench, dict) else bench.loc['max_drawdown', 'risk']

            f.write(f"| 平均日收益率 | {mean_val:.6f} |\n")
            f.write(f"| 收益标准差 | {std_val:.6f} |\n")
            f.write(f"| 年化收益率 | {ann_ret:.4%} |\n")
            f.write(f"| 信息比率（IR） | {ir:.4f} |\n")
            f.write(f"| 最大回撤 | {max_dd:.4%} |\n\n")

        # 策略收益（无成本）
        f.write("### 3.2 策略超额收益（无交易成本）\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("| --- | --- |\n")

        if 'excess_return_without_cost' in port_analysis:
            no_cost = port_analysis['excess_return_without_cost']
            mean_val = no_cost.get('mean', no_cost['risk'].get('mean', 0)) if isinstance(no_cost, dict) else no_cost.loc['mean', 'risk']
            std_val = no_cost.get('std', no_cost['risk'].get('std', 0)) if isinstance(no_cost, dict) else no_cost.loc['std', 'risk']
            ann_ret = no_cost.get('annualized_return', no_cost['risk'].get('annualized_return', 0)) if isinstance(no_cost, dict) else no_cost.loc['annualized_return', 'risk']
            ir = no_cost.get('information_ratio', no_cost['risk'].get('information_ratio', 0)) if isinstance(no_cost, dict) else no_cost.loc['information_ratio', 'risk']
            max_dd = no_cost.get('max_drawdown', no_cost['risk'].get('max_drawdown', 0)) if isinstance(no_cost, dict) else no_cost.loc['max_drawdown', 'risk']

            f.write(f"| 平均日收益率 | {mean_val:.6f} |\n")
            f.write(f"| 收益标准差 | {std_val:.6f} |\n")
            f.write(f"| 年化收益率 | {ann_ret:.4%} |\n")
            f.write(f"| 信息比率（IR） | {ir:.4f} |\n")
            f.write(f"| 最大回撤 | {max_dd:.4%} |\n\n")

        # 策略收益（含成本）
        f.write("### 3.3 策略超额收益（含交易成本）\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("| --- | --- |\n")

        if 'excess_return_with_cost' in port_analysis:
            with_cost = port_analysis['excess_return_with_cost']
            mean_val = with_cost.get('mean', with_cost['risk'].get('mean', 0)) if isinstance(with_cost, dict) else with_cost.loc['mean', 'risk']
            std_val = with_cost.get('std', with_cost['risk'].get('std', 0)) if isinstance(with_cost, dict) else with_cost.loc['std', 'risk']
            ann_ret = with_cost.get('annualized_return', with_cost['risk'].get('annualized_return', 0)) if isinstance(with_cost, dict) else with_cost.loc['annualized_return', 'risk']
            ir = with_cost.get('information_ratio', with_cost['risk'].get('information_ratio', 0)) if isinstance(with_cost, dict) else with_cost.loc['information_ratio', 'risk']
            max_dd = with_cost.get('max_drawdown', with_cost['risk'].get('max_drawdown', 0)) if isinstance(with_cost, dict) else with_cost.loc['max_drawdown', 'risk']

            f.write(f"| 平均日收益率 | {mean_val:.6f} |\n")
            f.write(f"| 收益标准差 | {std_val:.6f} |\n")
            f.write(f"| 年化收益率 | {ann_ret:.4%} |\n")
            f.write(f"| 信息比率（IR） | {ir:.4f} |\n")
            f.write(f"| 最大回撤 | {max_dd:.4%} |\n\n")

        # 其他指标
        if indicator_analysis is not None and not (isinstance(indicator_analysis, pd.DataFrame) and indicator_analysis.empty):
            f.write("### 3.4 其他交易指标\n\n")
            f.write("| 指标 | 数值 | 说明 |\n")
            f.write("| --- | --- | --- |\n")

            if isinstance(indicator_analysis, pd.DataFrame):
                ffr = indicator_analysis.loc['ffr', 'value'] if 'ffr' in indicator_analysis.index else 0
                pa = indicator_analysis.loc['pa', 'value'] if 'pa' in indicator_analysis.index else 0
                pos = indicator_analysis.loc['pos', 'value'] if 'pos' in indicator_analysis.index else 0
            else:
                ffr = indicator_analysis.get('ffr', 0)
                pa = indicator_analysis.get('pa', 0)
                pos = indicator_analysis.get('pos', 0)

            f.write(f"| FFR (持仓满仓率) | {ffr:.2f} | 持仓时间占总时间的比例 |\n")
            f.write(f"| PA (组合年化收益) | {pa:.4f} | Portfolio Annual Return |\n")
            f.write(f"| POS (持仓数) | {pos:.2f} | 平均持仓数量 |\n\n")

        # 生成收益曲线图
        f.write("## 4. 收益曲线\n\n")

        try:
            # 生成收益曲线图
            fig, ax = plt.subplots(figsize=(14, 7))

            # 从report_normal中获取收益数据
            if isinstance(report_normal, pd.DataFrame) and not report_normal.empty:
                # 计算累计收益
                if 'bench' in report_normal.columns:
                    bench_cum = (1 + report_normal['bench']).cumprod()
                    ax.plot(bench_cum.index, bench_cum.values, label='Benchmark (BTC/USDT)',
                           linewidth=2.5, color='#1f77b4')

                if 'return' in report_normal.columns:
                    strategy_cum = (1 + report_normal['return']).cumprod()
                    ax.plot(strategy_cum.index, strategy_cum.values, label='Strategy (含成本)',
                           linewidth=2.5, color='#ff7f0e')

            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('累计收益率', fontsize=12)
            ax.set_title('回测累计收益曲线对比', fontsize=14, fontweight='bold')
            ax.legend(loc='best', fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--')

            # 格式化x轴日期
            if len(bench_cum) > 0:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                plt.xticks(rotation=45)

            plt.tight_layout()

            # 保存图片
            img_path = output_dir / "returns_curve.png"
            plt.savefig(img_path, dpi=150, bbox_inches='tight')
            plt.close()

            f.write(f"![收益曲线](./returns_curve.png)\n\n")
            print(f"收益曲线图已保存到: {img_path}")

        except Exception as e:
            print(f"生成收益曲线图时出错: {e}")
            import traceback
            traceback.print_exc()
            f.write("*收益曲线图生成失败*\n\n")

        # 风险分析
        f.write("## 5. 风险分析\n\n")
        f.write("### 5.1 回撤分析\n\n")

        if 'excess_return_with_cost' in port_analysis:
            with_cost = port_analysis['excess_return_with_cost']
            max_dd = with_cost.get('max_drawdown', with_cost['risk'].get('max_drawdown', 0)) if isinstance(with_cost, dict) else with_cost.loc['max_drawdown', 'risk']
            f.write(f"- **最大回撤**: {max_dd:.4%}\n")
            f.write(f"- **风险评级**: {'高风险' if abs(max_dd) > 0.3 else '中等风险' if abs(max_dd) > 0.15 else '低风险'}\n\n")

        f.write("### 5.2 信息比率分析\n\n")

        if 'excess_return_with_cost' in port_analysis:
            with_cost = port_analysis['excess_return_with_cost']
            ir = with_cost.get('information_ratio', with_cost['risk'].get('information_ratio', 0)) if isinstance(with_cost, dict) else with_cost.loc['information_ratio', 'risk']
            f.write(f"- **信息比率（IR）**: {ir:.4f}\n")
            f.write(f"- **评级**: {'优秀' if ir > 1.0 else '良好' if ir > 0.5 else '一般' if ir > 0 else '较差'}\n\n")

        # 结论和建议
        f.write("## 6. 结论和建议\n\n")
        f.write("### 6.1 主要发现\n\n")

        # 基于实际指标生成结论
        if 'excess_return_with_cost' in port_analysis:
            with_cost = port_analysis['excess_return_with_cost']
            ann_ret = with_cost.get('annualized_return', with_cost['risk'].get('annualized_return', 0)) if isinstance(with_cost, dict) else with_cost.loc['annualized_return', 'risk']
            max_dd = with_cost.get('max_drawdown', with_cost['risk'].get('max_drawdown', 0)) if isinstance(with_cost, dict) else with_cost.loc['max_drawdown', 'risk']

            if ann_ret > 0:
                f.write(f"1. **正收益**: 策略在测试期间实现了 {ann_ret:.2%} 的年化收益率\n")
            else:
                f.write(f"1. **负收益**: 策略在测试期间表现欠佳，年化收益率为 {ann_ret:.2%}\n")

            f.write(f"2. **风险控制**: 最大回撤为 {max_dd:.2%}，显示策略在市场波动中的风险暴露\n")
            f.write(f"3. **交易成本影响**: 加密货币的交易成本对策略收益产生了显著影响\n")
            f.write(f"4. **模型表现**: 由于样本数量较少（仅2个交易对），Alpha158特征集的效果受到限制\n\n")

        f.write("### 6.2 优化建议\n\n")
        f.write("1. **特征工程**:\n")
        f.write("   - 考虑增加加密货币特有的指标（如链上数据、资金流向、情绪指标等）\n")
        f.write("   - 优化特征选择，减少噪声特征\n")
        f.write("   - 针对加密货币24/7交易特性设计专门的时间特征\n\n")
        f.write("2. **模型优化**:\n")
        f.write("   - 尝试使用深度学习模型（如LSTM、Transformer）更好地捕捉时序特征\n")
        f.write("   - 考虑集成学习方法，结合多个模型的预测结果\n")
        f.write("   - 增加训练数据量，扩展到更长的历史时期\n\n")
        f.write("3. **策略优化**:\n")
        f.write("   - 调整持仓比例和调仓频率，降低交易成本\n")
        f.write("   - 增加风险控制机制（如动态止损、仓位管理）\n")
        f.write("   - 考虑市场状态识别，在不同市场环境下采用不同策略\n")
        f.write("   - 增加更多交易对以提高策略的分散化效果\n\n")
        f.write("4. **数据扩展**:\n")
        f.write("   - 扩展到更多主流加密货币交易对（如SOL/USDT, BNB/USDT等）\n")
        f.write("   - 使用更长时间跨度的历史数据进行训练\n")
        f.write("   - 考虑使用高频数据（如小时线、15分钟线）捕捉短期波动\n\n")

        # 附录
        f.write("## 7. 附录\n\n")
        f.write("### 7.1 技术栈\n\n")
        f.write("- **量化平台**: Microsoft Qlib 0.9.8\n")
        f.write("- **数据来源**: Gate.io API v4\n")
        f.write("- **机器学习模型**: LightGBM 4.6.0\n")
        f.write("- **特征集**: Alpha158（158个技术指标）\n")
        f.write("- **编程语言**: Python 3.11\n")
        f.write("- **数据处理**: Pandas, NumPy\n")
        f.write("- **可视化**: Matplotlib\n")
        f.write("- **实验管理**: MLflow\n\n")

        f.write("### 7.2 关键指标说明\n\n")
        f.write("- **年化收益率（Annualized Return）**: 将测试期收益率按年化计算的收益率\n")
        f.write("- **信息比率（Information Ratio, IR）**: 超额收益与跟踪误差的比值，衡量风险调整后的收益\n")
        f.write("- **最大回撤（Max Drawdown）**: 从最高点到最低点的最大跌幅百分比\n")
        f.write("- **夏普比率**: 超额收益与波动率的比值（IR为其变体）\n")
        f.write("- **Alpha158**: Qlib内置的158个技术指标特征集，包含价格、成交量等多维度因子\n")
        f.write("- **FFR**: Full Fill Rate，持仓满仓率\n\n")

        f.write("### 7.3 数据说明\n\n")
        f.write("- 本回测基于Gate.io交易所的历史行情数据\n")
        f.write("- 数据时区：UTC+8（北京时间）\n")
        f.write("- 加密货币市场7×24小时交易，无休市日\n")
        f.write("- 交易成本设置：开仓0.1%，平仓0.1%\n\n")

        f.write("---\n\n")
        f.write("*报告生成完成*\n")

    print(f"\n✅ 报告已生成: {report_path}")
    return report_path


if __name__ == "__main__":
    generate_report()

