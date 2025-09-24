#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2022年のスケジュールをマスターファイルに追加
"""

import json
import os
from datetime import datetime

def add_year_schedule(master_file, year_data, year):
    """
    年度のスケジュールをマスターファイルに追加
    """
    # 既存のマスターを読み込み
    if os.path.exists(master_file):
        with open(master_file, 'r', encoding='utf-8') as f:
            master = json.load(f)
    else:
        master = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "period": "",
                "total_days": 0
            },
            "schedule_data": {}
        }

    # 新しいデータを追加
    added_count = 0
    for date_str, venues in year_data.items():
        if date_str not in master["schedule_data"]:
            master["schedule_data"][date_str] = venues
            added_count += 1

    # メタデータを更新
    all_dates = sorted(master["schedule_data"].keys())
    if all_dates:
        start_date = all_dates[0]
        end_date = all_dates[-1]
        master["metadata"]["period"] = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} to {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        master["metadata"]["total_days"] = len(all_dates)
        master["metadata"]["updated"] = datetime.now().isoformat()

    # ファイルに保存
    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    print(f"✅ {year}のスケジュール追加完了")
    print(f"   追加日数: {added_count}日")
    print(f"   総日数: {master['metadata']['total_days']}日")
    print(f"   期間: {master['metadata']['period']}")

    return master

# 2022年1月のデータ
def process_2022_01():
    """2022年1月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5,6,7日
    for day in [1,2,3,4,5,6,7]:
        schedule[f"202201{day:02d}"] = ["43"]

    # 船橋: 10,11,12,13,14日
    for day in [10,11,12,13,14]:
        schedule[f"202201{day:02d}"] = ["44"]

    # 浦和: 17,18,19,20,21日
    for day in [17,18,19,20,21]:
        schedule[f"202201{day:02d}"] = ["45"]

    # 大井: 24,25,26,27,28日（26日はDirt）
    for day in [24,25,26,27,28]:
        schedule[f"202201{day:02d}"] = ["42"]

    return schedule

# 2022年2月のデータ
def process_2022_02():
    """2022年2月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5日（2日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202202{day:02d}"] = ["43"]

    # 大井: 7,8,9,10,11日
    for day in [7,8,9,10,11]:
        schedule[f"202202{day:02d}"] = ["42"]

    # 船橋: 14,15,16,17,18日
    for day in [14,15,16,17,18]:
        schedule[f"202202{day:02d}"] = ["44"]

    # 浦和: 21,22,23,24,25日
    for day in [21,22,23,24,25]:
        schedule[f"202202{day:02d}"] = ["45"]

    return schedule

# 2022年3月のデータ
def process_2022_03():
    """2022年3月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4日（2日はDirt）
    for day in [1,2,3,4]:
        schedule[f"202203{day:02d}"] = ["43"]

    # 大井: 7,8,9,10,11日
    for day in [7,8,9,10,11]:
        schedule[f"202203{day:02d}"] = ["42"]

    # 浦和: 14,15,16,17,18日
    for day in [14,15,16,17,18]:
        schedule[f"202203{day:02d}"] = ["45"]

    # 船橋: 21,22,23,24,25日（23日はDirt）
    for day in [21,22,23,24,25]:
        schedule[f"202203{day:02d}"] = ["44"]

    return schedule

# 2022年4月のデータ
def process_2022_04():
    """2022年4月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4,5,6日（4日はDirt）
    for day in [1,2,3,4,5,6]:
        schedule[f"202204{day:02d}"] = ["42"]

    # 川崎: 8,9,10,11,12日
    for day in [8,9,10,11,12]:
        schedule[f"202204{day:02d}"] = ["43"]

    # 船橋: 13,14,15,16,17日（15日はDirt）
    for day in [13,14,15,16,17]:
        schedule[f"202204{day:02d}"] = ["44"]

    # 浦和: 25,26,27,28,29日
    for day in [25,26,27,28,29]:
        schedule[f"202204{day:02d}"] = ["45"]

    return schedule

# 2022年5月のデータ
def process_2022_05():
    """2022年5月のスケジュールデータ"""
    schedule = {}

    # 船橋: 2,3,4,5,6日（4日はDirt）
    for day in [2,3,4,5,6]:
        schedule[f"202205{day:02d}"] = ["44"]

    # 大井: 9,10,11,12,13日、16,17,18,19,20日
    for day in [9,10,11,12,13,16,17,18,19,20]:
        schedule[f"202205{day:02d}"] = ["42"]

    # 川崎: 23,24,25,26,27日
    for day in [23,24,25,26,27]:
        schedule[f"202205{day:02d}"] = ["43"]

    # 浦和: 30,31日
    for day in [30,31]:
        schedule[f"202205{day:02d}"] = ["45"]

    return schedule

# 2022年6月のデータ
def process_2022_06():
    """2022年6月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2日（1日はDirt）
    for day in [1,2]:
        schedule[f"202206{day:02d}"] = ["45"]

    # 大井: 6,7,8,9,10日、13,14,15日（14日はDirt）
    for day in [6,7,8,9,10,13,14,15]:
        schedule[f"202206{day:02d}"] = ["42"]

    # 川崎: 16,17,18,19,20日（18日はDirt）
    for day in [16,17,18,19,20]:
        schedule[f"202206{day:02d}"] = ["43"]

    # 船橋: 21,22,23,24,25日
    for day in [21,22,23,24,25]:
        schedule[f"202206{day:02d}"] = ["44"]

    return schedule

# 2022年7月のデータ
def process_2022_07():
    """2022年7月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2日
    for day in [1,2]:
        schedule[f"202207{day:02d}"] = ["45"]

    # 大井: 1日、4,5,6,7,8日（5日はDirt）、11,12,13日
    schedule[f"20220701"] = ["42"]
    for day in [4,5,6,7,8,11,12,13]:
        schedule[f"202207{day:02d}"] = ["42"]

    # 川崎: 14,15,16,17,18日（16日はDirt）
    for day in [14,15,16,17,18]:
        schedule[f"202207{day:02d}"] = ["43"]

    # 船橋: 25,26,27,28,29日
    for day in [25,26,27,28,29]:
        schedule[f"202207{day:02d}"] = ["44"]

    return schedule

# 2022年8月のデータ
def process_2022_08():
    """2022年8月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5日、8,9,10日
    for day in [1,2,3,4,5,8,9,10]:
        schedule[f"202208{day:02d}"] = ["43"]

    # 浦和: 15,16,17,18,19,20,21日
    for day in [15,16,17,18,19,20,21]:
        schedule[f"202208{day:02d}"] = ["45"]

    # 大井: 22,23,24,25,26,27日
    for day in [22,23,24,25,26,27]:
        schedule[f"202208{day:02d}"] = ["42"]

    # 船橋: 29,30,31日
    for day in [29,30,31]:
        schedule[f"202208{day:02d}"] = ["44"]

    return schedule

# 2022年9月のデータ
def process_2022_09():
    """2022年9月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5日（4日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202209{day:02d}"] = ["45"]

    # 大井: 9,10,11,12,13日、16,17,18,19,20日
    for day in [9,10,11,12,13,16,17,18,19,20]:
        schedule[f"202209{day:02d}"] = ["42"]

    # 川崎: 21,22,23,24,25日
    for day in [21,22,23,24,25]:
        schedule[f"202209{day:02d}"] = ["43"]

    # 船橋: 26,27,28,29,30日（28日はDirt）
    for day in [26,27,28,29,30]:
        schedule[f"202209{day:02d}"] = ["44"]

    return schedule

# 2022年10月のデータ
def process_2022_10():
    """2022年10月のスケジュールデータ"""
    schedule = {}

    # 大井: 3,4,5,6,7日（5,6日はDirt）、10,11日
    for day in [3,4,5,6,7,10,11]:
        schedule[f"202210{day:02d}"] = ["42"]

    # 川崎: 12,13,14,15,16日
    for day in [12,13,14,15,16]:
        schedule[f"202210{day:02d}"] = ["43"]

    # 浦和: 24,25,26,27,28日
    for day in [24,25,26,27,28]:
        schedule[f"202210{day:02d}"] = ["45"]

    # 船橋: 31日
    schedule[f"20221031"] = ["44"]

    return schedule

# 2022年11月のデータ
def process_2022_11():
    """2022年11月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3日（3日はDirt）
    for day in [1,2,3]:
        schedule[f"202211{day:02d}"] = ["44"]

    # 大井: 1,2,3,4日、7,8,9,10,11日
    for day in [1,2,3,4,7,8,9,10,11]:
        schedule[f"202211{day:02d}"] = ["42"]

    # 川崎: 14,15,16,17,18日
    for day in [14,15,16,17,18]:
        schedule[f"202211{day:02d}"] = ["43"]

    # 浦和: 21,22,23,24,25日（23日はDirt）
    for day in [21,22,23,24,25]:
        schedule[f"202211{day:02d}"] = ["45"]

    return schedule

# 2022年12月のデータ
def process_2022_12():
    """2022年12月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3,4,5,6,7,8日
    for day in [1,2,3,4,5,6,7,8]:
        schedule[f"202212{day:02d}"] = ["44"]

    # 大井: 12,13,14,15,16,17,18,19,20日（19日はDirt）、29,30,31日
    for day in [12,13,14,15,16,17,18,19,20,29,30,31]:
        schedule[f"202212{day:02d}"] = ["42"]

    # 川崎: 21,22,23,24,25日（23日はDirt）
    for day in [21,22,23,24,25]:
        schedule[f"202212{day:02d}"] = ["43"]

    # 浦和: 26,27,28,29日
    for day in [26,27,28,29]:
        schedule[f"202212{day:02d}"] = ["45"]

    return schedule

if __name__ == "__main__":
    master_file = "/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json"

    print("="*60)
    print("2022年スケジュールマスター更新開始")
    print("="*60)

    # 2022年1月を追加
    jan_2022 = process_2022_01()
    add_year_schedule(master_file, jan_2022, "2022年1月")

    # 2022年2月を追加
    feb_2022 = process_2022_02()
    add_year_schedule(master_file, feb_2022, "2022年2月")

    # 2022年3月を追加
    mar_2022 = process_2022_03()
    add_year_schedule(master_file, mar_2022, "2022年3月")

    # 2022年4月を追加
    apr_2022 = process_2022_04()
    add_year_schedule(master_file, apr_2022, "2022年4月")

    # 2022年5月を追加
    may_2022 = process_2022_05()
    add_year_schedule(master_file, may_2022, "2022年5月")

    # 2022年6月を追加
    jun_2022 = process_2022_06()
    add_year_schedule(master_file, jun_2022, "2022年6月")

    # 2022年7月を追加
    jul_2022 = process_2022_07()
    add_year_schedule(master_file, jul_2022, "2022年7月")

    # 2022年8月を追加
    aug_2022 = process_2022_08()
    add_year_schedule(master_file, aug_2022, "2022年8月")

    # 2022年9月を追加
    sep_2022 = process_2022_09()
    add_year_schedule(master_file, sep_2022, "2022年9月")

    # 2022年10月を追加
    oct_2022 = process_2022_10()
    add_year_schedule(master_file, oct_2022, "2022年10月")

    # 2022年11月を追加
    nov_2022 = process_2022_11()
    add_year_schedule(master_file, nov_2022, "2022年11月")

    # 2022年12月を追加
    dec_2022 = process_2022_12()
    add_year_schedule(master_file, dec_2022, "2022年12月")

    print("\n✅ 2022年のスケジュール追加が完了しました！")