def plot_weeks_compare(agg_df, output_dir, 意图名称, week_names):
    """
    多周对比柱状图，每个模型的week3/4紧邻排列
    agg_df: 包含['大模型', '推荐率', '前三率', '置顶率', 'week']，每行是一个模型/一周
    week_names: 如 ["Week3", "Week4"]
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from matplotlib.ticker import FuncFormatter

    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']  # 中文字体
    plt.rcParams['axes.unicode_minus'] = False

    # 1. 排序，确保同一模型的不同week排列在一起
    agg_df = agg_df.copy()
    agg_df['week'] = agg_df['week'].astype(str)
    agg_df = agg_df.sort_values(["大模型", "week"], ascending=[True, True])
    agg_df['模型周'] = agg_df['大模型'].astype(str) + '\n' + agg_df['week']

    models_weeks = agg_df['模型周'].tolist()
    data = agg_df[['推荐率', '前三率', '置顶率']].values * 100

    n = len(models_weeks)
    bar_width = 0.28
    x = np.arange(n)
    colors = ['#67D6CA', '#3283FF', '#002CB0']
    labels = ['推荐率', '前三率', '置顶率']

    fig, ax = plt.subplots(figsize=(max(n * 0.9, 10), 6))

    # 画每一种指标的柱
    for i in range(3):
        ax.bar(x + i * bar_width, data[:, i], width=bar_width, color=colors[i], label=labels[i])
        for j in range(n):
            val = data[j, i]
            if not np.isnan(val):
                ax.text(x[j] + i * bar_width, val + 1.2, f"{val:.2f}", ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xticks(x + bar_width)
    ax.set_xticklabels(models_weeks, rotation=40, ha='right', fontsize=12)
    ax.set_ylabel('百分比 (%)', fontsize=13)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}%"))

    # 主副标题
    ax.set_title(意图名称, fontsize=18, fontweight='bold', loc='left', pad=30)
    subtitle = f"{'/'.join(week_names)} 各大模型三率对比"
    ax.text(0, 1.02, subtitle,
            transform=ax.transAxes,
            fontsize=12,
            color='#888888',
            ha='left',
            va='baseline')

    # 图例
    ax.legend(
        fontsize=12,
        ncol=1,
        loc='upper left',
        bbox_to_anchor=(1.01, 1),
        borderaxespad=0.,
        frameon=True
    )
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    png_file = f"{output_dir}/bar_{意图名称}_{'-'.join(week_names)}.png"
    plt.savefig(png_file, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"已导出柱状图到: {png_file}")