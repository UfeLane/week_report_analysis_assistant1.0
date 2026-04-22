import pandas as pd
import os
from utils.plotter import plot_weeks_compare

def get_week_data_for_all(df, week_settings):
    week_data_dict = {}
    for week_num, (start, end) in week_settings.items():
        week_str = f"Week{week_num}"
        try:
            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
        except:
            print(f"Week{week_num}的日期格式有误！")
            week_data_dict[week_num] = (None, week_str)
            continue
        mask = (df['时间'] >= start_dt) & (df['时间'] <= end_dt)
        week_data = df.loc[mask].copy()
        week_data['week'] = week_str
        week_data_dict[week_num] = (week_data, week_str)
    return week_data_dict

def main():
    # ==================
    # 检查是否已有聚合数据
    # ==================
    GLOBAL_AGG = None
    if 'all_agg' in globals():
        try:
            GLOBAL_AGG = globals()['all_agg']
            reuse = input("检测到已有聚合数据（all_agg），是否直接用它进行画图？(y/n)：").strip().lower()
        except Exception as e:
            reuse = 'n'
        if reuse == 'y':
            意图名称 = input("请输入分析意图名称：").strip()
            output_dir = input("请输入图片导出目录（如'output/reports'）：").strip()
            week_names = input("请输入参与的week名（英文逗号分隔，如'Week3,Week4'）：").split(',')
            plot_weeks_compare(GLOBAL_AGG, output_dir, 意图名称, week_names)
            print('绘图完毕。')
            return

    # ==================
    # 数据加载流程
    # ==================
    raw_path = input("请输入原始数据文件的绝对路径（支持xlsx/xls/csv）：\n")
    path = raw_path.strip().strip('"').strip("'").strip('“').strip('”')
    if not os.path.exists(path):
        print(f"文件未找到：{path}")
        return

    try:
        if path.lower().endswith('.csv'):
            df = pd.read_csv(path, encoding='utf-8-sig', sep=None, engine='python')
        elif path.lower().endswith('.xlsx') or path.lower().endswith('.xls'):
            df = pd.read_excel(path)
        else:
            print("仅支持csv、xlsx、xls文件！")
            return
    except Exception as e:
        print(f"文件读取失败：{e}")
        return

    # 时间字段转日期
    if '时间' not in df.columns:
        print(f"数据缺少 '时间' 字段，实际字段：{list(df.columns)}")
        return
    try:
        df['时间'] = pd.to_datetime(df['时间'])
    except Exception as e:
        print(f"无法将时间字段转为日期类型，错误：{e}")
        return

    if '意图问题' not in df.columns:
        print("缺少 '意图问题' 字段！")
        return

    required_columns = [
        '大模型', '提问次数', '推荐次数', '前三名次数', '第一名次数',
        # 引用相关指标
        '总引用文章篇次', '我司发布文章总引用篇次', '总引用文章篇数', '我司发布文章总引用篇数',
        '正文引用文章篇次', '我司发布文章正文引用篇次', '正文引用文章篇数', '我司发布文章正文引用篇数'
    ]
    for col in required_columns:
        if col not in df.columns:
            print(f"缺失字段：{col}")
            return

    # ========== 只输入一次week划分 ==========
    week_nums_raw = input("\n请输入统计周编号week（如3,或3 4，多周用英文逗号/空格分隔）：").strip()
    week_nums_raw = week_nums_raw.replace('，', ',').replace(' ', ',')
    week_nums = [w for w in week_nums_raw.split(',') if w.isdigit()]
    if len(week_nums) == 0:
        print("周次输入有误！")
        return

    week_settings = {}
    for week_num in week_nums:
        start = input(f"请输入第{week_num}周的起始日期（如2026-04-08）：").strip()
        end = input(f"请输入第{week_num}周的结束日期（如2026-04-14）：").strip()
        week_settings[week_num] = (start, end)

    # ========== 按意图分析循环 ==========
    while True:
        意图列表 = df['意图问题'].unique()
        print("\n可选意图如下：")
        for idx, name in enumerate(意图列表):
            print(f"{idx + 1}. {name}")

        try:
            意图idx = int(input("请输入要分析的意图序号：").strip()) - 1
            if 意图idx < 0 or 意图idx >= len(意图列表):
                print("序号超范围！")
                continue
            意图名称 = 意图列表[意图idx]
        except:
            print("输入有误，请输入数字序号！")
            continue

        意图_data = df[df['意图问题'] == 意图名称]
        if 意图_data.empty:
            print("该意图在所有数据中无数据！")
            continue

        # 全部转数值类型
        num_fields = [
            '提问次数', '推荐次数', '前三名次数', '第一名次数',
            # 引用相关字段
            '总引用文章篇次', '我司发布文章总引用篇次', '总引用文章篇数', '我司发布文章总引用篇数',
            '正文引用文章篇次', '我司发布文章正文引用篇次', '正文引用文章篇数', '我司发布文章正文引用篇数'
        ]
        for col in num_fields:
            if col in 意图_data.columns:
                意图_data[col] = pd.to_numeric(意图_data[col], errors='coerce')

        # 自动补充占比和强度衍生字段
        意图_data['我司正文引用占比（次数口径）'] = 意图_data['我司发布文章正文引用篇次'] / 意图_data['正文引用文章篇次']
        意图_data['我司正文引用占比（篇数口径）'] = 意图_data['我司发布文章正文引用篇数'] / 意图_data['正文引用文章篇数']
        # "我司正文引用强度"为例（可根据实际业务公式调整）
        意图_data['我司正文引用强度'] = 意图_data['我司发布文章正文引用篇次'] / 意图_data['提问次数']

        week_data_dict = get_week_data_for_all(意图_data, week_settings)

        agg_list = []
        week_str_list = []
        for week_num in week_nums:
            week_data, week_str = week_data_dict[week_num]
            if week_data is None or week_data.empty:
                print(f"{week_str}未筛选到数据！")
                continue
            agg = week_data.groupby('大模型').agg({
                '提问次数': 'sum',
                '推荐次数': 'sum',
                '前三名次数': 'sum',
                '第一名次数': 'sum',
                # 引用相关聚合
                '总引用文章篇次': 'sum',
                '我司发布文章总引用篇次': 'sum',
                '总引用文章篇数': 'sum',
                '我司发布文章总引用篇数': 'sum',
                '正文引用文章篇次': 'sum',
                '我司发布文章正文引用篇次': 'sum',
                '正文引用文章篇数': 'sum',
                '我司发布文章正文引用篇数': 'sum',
                '我司正文引用占比（次数口径）': 'mean',
                '我司正文引用占比（篇数口径）': 'mean',
                '我司正文引用强度': 'mean',
            }).reset_index()
            # 主要业务衍生字段
            agg['推荐率'] = agg['推荐次数'] / agg['提问次数']
            agg['前三率'] = agg['前三名次数'] / agg['提问次数']
            agg['置顶率'] = agg['第一名次数'] / agg['提问次数']
            agg['week'] = week_str
            agg_list.append(agg)
            week_str_list.append(week_str)

        if not agg_list:
            print("所有区间都无数据！")
            continue

        all_agg = pd.concat(agg_list, ignore_index=True)

        # 环比（只对两周做）
        if len(week_nums) == 2:
            weekA = f"Week{week_nums[0]}"
            weekB = f"Week{week_nums[1]}"
            dfA = all_agg[all_agg['week'] == weekA].set_index('大模型')
            dfB = all_agg[all_agg['week'] == weekB].set_index('大模型')
            # 环比指标列表
            rate_fields = [
                '推荐率', '前三率', '置顶率',
                '我司正文引用强度',
                '我司正文引用占比（次数口径）',
                '我司正文引用占比（篇数口径）',
            ]
            for rate in rate_fields:
                valid_models = set(dfA.index) & set(dfB.index)
                for model in valid_models:
                    base = dfA.loc[model, rate]
                    now = dfB.loc[model, rate]
                    if pd.notnull(base) and pd.notnull(now) and base != 0:
                        try:
                            val = round((now - base) / base * 100, 2)
                            if np.isinf(val) or np.isnan(val):
                                val = None
                        except:
                            val = None
                    else:
                        val = None
                    all_agg.loc[(all_agg['大模型'] == model) & (all_agg['week'] == weekB), rate + '_增速'] = val

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(BASE_DIR, 'output', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        print(f"输出目录已准备：{output_dir}")
        outcsv = f"{output_dir}/multi_statistics_{意图名称}_{'_'.join(week_str_list)}.csv"
        all_agg.to_csv(outcsv, index=False, encoding='utf-8-sig')
        print(f"已导出统计数据: {outcsv}")

        plot_weeks_compare(all_agg, output_dir, 意图名称, week_str_list)

        goon = input("\n是否要继续分析其他意图？(y/n)：").strip().lower()
        if goon != 'y':
            print("已退出。")
            break

if __name__ == "__main__":
    main()
