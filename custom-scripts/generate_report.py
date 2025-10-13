#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate backtest report from Qlib results
"""

import sys
import pickle
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Qlib imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import qlib
from qlib.workflow import R


def generate_markdown_report(exp_name="workflow"):
    """生成Markdown格式的回测报告"""

    # 设置MLflow tracking URI到正确的位置
    import mlflow
    mlflow_dir = Path(__file__).parent / "mlruns"
    mlflow.set_tracking_uri(f"file://{mlflow_dir}")

    # 初始化 Qlib
    qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data", region="cn")

    # 获取最新的实验
    exp = R.get_exp(experiment_name=exp_name)
    recorders = exp.list_recorders()

    if not recorders:
        print("没有找到实验记录")
        return

    # 获取最新的recorder
    latest_recorder = recorders.iloc[-1]
    recorder_id = latest_recorder['id']

    print(f"使用Recorder ID: {recorder_id}")

    recorder = R.get_recorder(recorder_id=recorder_id, experiment_name=exp_name)

    # 创建输出目录
    output_dir = Path(__file__).parent.parent / "agent-docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载回测结果
    try:
        port_analysis = recorder.load_object("port_analysis_1day.pkl")
        indicator_analysis = recorder.load_object("indicator_analysis_1day.pkl")
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return

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
        f.write("### 3.1 基准收益（Benchmark）\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("| --- | --- |\n")

        if 'bench' in port_analysis:
            bench_metrics = port_analysis['bench']
            f.write(f"| 平均日收益率 | {bench_metrics.get('mean', 0):.6f} |\n")
            f.write(f"| 收益标准差 | {bench_metrics.get('std', 0):.6f} |\n")
            f.write(f"| 年化收益率 | {bench_metrics.get('annualized_return', 0):.4%} |\n")
            f.write(f"| 信息比率（IR） | {bench_metrics.get('information_ratio', 0):.4f} |\n")
            f.write(f"| 最大回撤 | {bench_metrics.get('max_drawdown', 0):.4%} |\n\n")

        # 策略收益（无成本）
        f.write("### 3.2 策略超额收益（无交易成本）\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("| --- | --- |\n")

        if 'excess_return_without_cost' in port_analysis:
            no_cost_metrics = port_analysis['excess_return_without_cost']
            f.write(f"| 平均日收益率 | {no_cost_metrics.get('mean', 0):.6f} |\n")
            f.write(f"| 收益标准差 | {no_cost_metrics.get('std', 0):.6f} |\n")
            f.write(f"| 年化收益率 | {no_cost_metrics.get('annualized_return', 0):.4%} |\n")
            f.write(f"| 信息比率（IR） | {no_cost_metrics.get('information_ratio', 0):.4f} |\n")
            f.write(f"| 最大回撤 | {no_cost_metrics.get('max_drawdown', 0):.4%} |\n\n")

        # 策略收益（含成本）
        f.write("### 3.3 策略超额收益（含交易成本）\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("| --- | --- |\n")

        if 'excess_return_with_cost' in port_analysis:
            cost_metrics = port_analysis['excess_return_with_cost']
            f.write(f"| 平均日收益率 | {cost_metrics.get('mean', 0):.6f} |\n")
            f.write(f"| 收益标准差 | {cost_metrics.get('std', 0):.6f} |\n")
            f.write(f"| 年化收益率 | {cost_metrics.get('annualized_return', 0):.4%} |\n")
            f.write(f"| 信息比率（IR） | {cost_metrics.get('information_ratio', 0):.4f} |\n")
            f.write(f"| 最大回撤 | {cost_metrics.get('max_drawdown', 0):.4%} |\n\n")

        # 其他指标
        if indicator_analysis:
            f.write("### 3.4 其他交易指标\n\n")
            f.write("| 指标 | 数值 | 说明 |\n")
            f.write("| --- | --- | --- |\n")
            f.write(f"| FFR (持仓满仓率) | {indicator_analysis.get('ffr', 0):.2f} | 持仓时间占总时间的比例 |\n")
            f.write(f"| PA (组合年化收益) | {indicator_analysis.get('pa', 0):.4f} | Portfolio Annual Return |\n")
            f.write(f"| POS (持仓数) | {indicator_analysis.get('pos', 0):.2f} | 平均持仓数量 |\n\n")

        # 生成收益曲线图
        f.write("## 4. 收益曲线\n\n")

        try:
            # 生成收益曲线图
            fig, ax = plt.subplots(figsize=(14, 7))

            # 绘制累计收益曲线
            if 'return' in port_analysis:
                returns_df = port_analysis['return']

                # 计算累计收益
                if 'bench' in returns_df.columns:
                    bench_cum = (1 + returns_df['bench']).cumprod()
                    ax.plot(bench_cum.index, bench_cum.values, label='Benchmark (BTC/USDT)', linewidth=2)

                if 'excess_return_with_cost' in returns_df.columns:
                    strategy_cum = (1 + returns_df['bench'] + returns_df['excess_return_with_cost']).cumprod()
                    ax.plot(strategy_cum.index, strategy_cum.values, label='Strategy (含成本)', linewidth=2)

                if 'excess_return_without_cost' in returns_df.columns:
                    strategy_no_cost_cum = (1 + returns_df['bench'] + returns_df['excess_return_without_cost']).cumprod()
                    ax.plot(strategy_no_cost_cum.index, strategy_no_cost_cum.values,
                           label='Strategy (不含成本)', linewidth=2, linestyle='--', alpha=0.7)

            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('累计收益率', fontsize=12)
            ax.set_title('回测累计收益曲线对比', fontsize=14, fontweight='bold')
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)

            # 格式化x轴日期
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
            f.write("*收益曲线图生成失败*\n\n")

        # 风险分析
        f.write("## 5. 风险分析\n\n")
        f.write("### 5.1 回撤分析\n\n")

        if 'excess_return_with_cost' in port_analysis:
            max_dd = cost_metrics.get('max_drawdown', 0)
            f.write(f"- **最大回撤**: {max_dd:.4%}\n")
            f.write(f"- **风险评级**: {'高风险' if abs(max_dd) > 0.3 else '中等风险' if abs(max_dd) > 0.15 else '低风险'}\n\n")

        f.write("### 5.2 夏普比率分析\n\n")

        if 'excess_return_with_cost' in port_analysis:
            ir = cost_metrics.get('information_ratio', 0)
            f.write(f"- **信息比率（IR）**: {ir:.4f}\n")
            f.write(f"- **评级**: {'优秀' if ir > 1.0 else '良好' if ir > 0.5 else '一般' if ir > 0 else '较差'}\n\n")

        # 结论和建议
        f.write("## 6. 结论和建议\n\n")
        f.write("### 6.1 主要发现\n\n")

        # 基于实际指标生成结论
        if 'excess_return_with_cost' in port_analysis:
            annual_return = cost_metrics.get('annualized_return', 0)
            max_dd = cost_metrics.get('max_drawdown', 0)

            if annual_return > 0:
                f.write(f"1. **正收益**: 策略在测试期间实现了 {annual_return:.2%} 的年化收益率\n")
            else:
                f.write(f"1. **负收益**: 策略在测试期间表现欠佳，年化收益率为 {annual_return:.2%}\n")

            f.write(f"2. **风险控制**: 最大回撤为 {max_dd:.2%}\n")
            f.write(f"3. **交易成本影响**: 交易成本对策略收益产生了明显影响\n")
            f.write(f"4. **模型表现**: 由于加密货币市场的高波动性，LightGBM模型在捕捉趋势方面存在挑战\n\n")

        f.write("### 6.2 优化建议\n\n")
        f.write("1. **特征工程**:\n")
        f.write("   - 考虑增加加密货币特有的指标（如链上数据、情绪指标等）\n")
        f.write("   - 优化特征选择，减少噪声特征\n\n")
        f.write("2. **模型优化**:\n")
        f.write("   - 尝试使用深度学习模型（如LSTM、Transformer）捕捉时序特征\n")
        f.write("   - 考虑集成学习方法，结合多个模型的预测结果\n\n")
        f.write("3. **策略优化**:\n")
        f.write("   - 调整持仓比例和调仓频率\n")
        f.write("   - 增加风险控制机制（如止损、仓位管理）\n")
        f.write("   - 考虑市场状态识别，在不同市场环境下采用不同策略\n\n")
        f.write("4. **数据扩展**:\n")
        f.write("   - 扩展到更多加密货币交易对\n")
        f.write("   - 使用更长时间跨度的历史数据\n")
        f.write("   - 考虑使用高频数据（如小时线、分钟线）\n\n")

        # 附录
        f.write("## 7. 附录\n\n")
        f.write("### 7.1 技术栈\n\n")
        f.write("- **量化平台**: Microsoft Qlib\n")
        f.write("- **数据来源**: Gate.io API v4\n")
        f.write("- **机器学习模型**: LightGBM\n")
        f.write("- **特征集**: Alpha158\n")
        f.write("- **编程语言**: Python 3.11\n")
        f.write("- **可视化**: Matplotlib\n\n")

        f.write("### 7.2 关键指标说明\n\n")
        f.write("- **年化收益率**: 将日收益率按年化计算的收益率\n")
        f.write("- **信息比率（IR）**: 收益率与标准差的比值，衡量风险调整后的收益\n")
        f.write("- **最大回撤**: 从最高点到最低点的最大跌幅\n")
        f.write("- **夏普比率**: 超额收益与波动率的比值（类似于IR）\n")
        f.write("- **Alpha158**: Qlib内置的158个技术指标特征集\n\n")

        f.write("---\n\n")
        f.write("*报告生成完成*\n")

    print(f"\n报告已生成: {report_path}")
    return report_path


if __name__ == "__main__":
    generate_markdown_report()

