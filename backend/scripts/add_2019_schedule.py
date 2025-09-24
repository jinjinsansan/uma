#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2019年のスケジュールをマスターファイルに追加
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

# 2019年1月のデータ
def process_2019_01():
    """2019年1月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5,6,8,9日（7日はDirt）
    for day in [1,2,3,4,5,6,8,9]:
        schedule[f"201901{day:02d}"] = ["43"]

    # 浦和: 14,15,16,17,18日
    for day in [14,15,16,17,18]:
        schedule[f"201901{day:02d}"] = ["45"]

    # 船橋: 21,22,23,24日
    for day in [21,22,23,24]:
        schedule[f"201901{day:02d}"] = ["44"]

    # 大井: 25,26,27,28,29日（27日はDirt）
    for day in [25,26,27,28,29]:
        schedule[f"201901{day:02d}"] = ["42"]

    return schedule

# 2019年2月のデータ
def process_2019_02():
    """2019年2月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5日（4日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"201902{day:02d}"] = ["43"]

    # 大井: 8,9,10,11,12日
    for day in [8,9,10,11,12]:
        schedule[f"201902{day:02d}"] = ["42"]

    # 浦和: 15,16,17,18,19日
    for day in [15,16,17,18,19]:
        schedule[f"201902{day:02d}"] = ["45"]

    # 船橋: 23,24,25,26,27日
    for day in [23,24,25,26,27]:
        schedule[f"201902{day:02d}"] = ["44"]

    return schedule

# 2019年3月のデータ
def process_2019_03():
    """2019年3月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1日
    schedule[f"20190301"] = ["43"]

    # 大井: 4,5,6,7,8,9,10,11,12,13日
    for day in [4,5,6,7,8,9,10,11,12,13]:
        schedule[f"201903{day:02d}"] = ["42"]

    # 船橋: 15,16,17,18,19日（17日はDirt）
    for day in [15,16,17,18,19]:
        schedule[f"201903{day:02d}"] = ["44"]

    # 浦和: 25,26,27,28,29日
    for day in [25,26,27,28,29]:
        schedule[f"201903{day:02d}"] = ["45"]

    return schedule

# 2019年4月のデータ
def process_2019_04():
    """2019年4月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5日
    for day in [1,2,3,4,5]:
        schedule[f"201904{day:02d}"] = ["43"]

    # 大井: 15,16,17,18,19,20,21,22,23,24日（17日はDirt）
    for day in [15,16,17,18,19,20,21,22,23,24]:
        schedule[f"201904{day:02d}"] = ["42"]

    # 船橋: 20,21,22,23,24日（22日はDirt）
    for day in [20,21,22,23,24]:
        schedule[f"201904{day:02d}"] = ["44"]

    # 浦和: 30日
    schedule[f"20190430"] = ["45"]

    return schedule

# 2019年5月のデータ
def process_2019_05():
    """2019年5月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5,6,7,8日（6日はDirt）
    for day in [1,2,3,4,5,6,7,8]:
        schedule[f"201905{day:02d}"] = ["45"]

    # 船橋: 13,14,15,16,17日（13日はDirt）
    for day in [13,14,15,16,17]:
        schedule[f"201905{day:02d}"] = ["44"]

    # 川崎: 20,21,22,23,24日
    for day in [20,21,22,23,24]:
        schedule[f"201905{day:02d}"] = ["43"]

    # 大井: 27,28,29,30,31日
    for day in [27,28,29,30,31]:
        schedule[f"201905{day:02d}"] = ["42"]

    return schedule

# 2019年6月のデータ
def process_2019_06():
    """2019年6月のスケジュールデータ"""
    schedule = {}

    # 大井: 5,6,7,8,9,10,11,12,13,14日（12日はDirt）
    for day in [5,6,7,8,9,10,11,12,13,14]:
        schedule[f"201906{day:02d}"] = ["42"]

    # 川崎: 17,18,19,20,21日（19日はDirt）
    for day in [17,18,19,20,21]:
        schedule[f"201906{day:02d}"] = ["43"]

    # 船橋: 22,23,24,25,26日
    for day in [22,23,24,25,26]:
        schedule[f"201906{day:02d}"] = ["44"]

    # 浦和: 28,29日
    for day in [28,29]:
        schedule[f"201906{day:02d}"] = ["45"]

    return schedule

# 2019年7月のデータ
def process_2019_07():
    """2019年7月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4日
    for day in [1,2,3,4]:
        schedule[f"201907{day:02d}"] = ["45"]

    # 川崎: 3,4,5,6,7,8,9,10日（5日はDirt）
    for day in [3,4,5,6,7,8,9,10]:
        schedule[f"201907{day:02d}"] = ["43"]

    # 大井: 15,16,17,18,19,20,21,22,23日（17日はDirt）
    for day in [15,16,17,18,19,20,21,22,23]:
        schedule[f"201907{day:02d}"] = ["42"]

    # 船橋: 22,23,24,25日
    for day in [22,23,24,25]:
        schedule[f"201907{day:02d}"] = ["44"]

    return schedule

# 2019年8月のデータ
def process_2019_08():
    """2019年8月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4,5,6,7,8,9,10,11日
    for day in [1,2,3,4,5,6,7,8,9,10,11]:
        schedule[f"201908{day:02d}"] = ["42"]

    # 川崎: 3,4,5,6,7,8日
    for day in [3,4,5,6,7,8]:
        schedule[f"201908{day:02d}"] = ["43"]

    # 船橋: 13,14,15,16,17,18,19日
    for day in [13,14,15,16,17,18,19]:
        schedule[f"201908{day:02d}"] = ["44"]

    # 浦和: 16,17,18日
    for day in [16,17,18]:
        schedule[f"201908{day:02d}"] = ["45"]

    return schedule

# 2019年9月のデータ
def process_2019_09():
    """2019年9月のスケジュールデータ"""
    schedule = {}

    # 船橋: 2,3,4,5,6,7日（3日はDirt）
    for day in [2,3,4,5,6,7]:
        schedule[f"201909{day:02d}"] = ["44"]

    # 川崎: 5,6,7,8日
    for day in [5,6,7,8]:
        schedule[f"201909{day:02d}"] = ["43"]

    # 浦和: 16,17,18,19,20日（19日はDirt）
    for day in [16,17,18,19,20]:
        schedule[f"201909{day:02d}"] = ["45"]

    # 大井: 23,24,25,26,27,28日
    for day in [23,24,25,26,27,28]:
        schedule[f"201909{day:02d}"] = ["42"]

    return schedule

# 2019年10月のデータ
def process_2019_10():
    """2019年10月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4,5,6,7,8,9日（2,3日はDirt）
    for day in [1,2,3,4,5,6,7,8,9]:
        schedule[f"201910{day:02d}"] = ["42"]

    # 浦和: 14,15,16,17,18日
    for day in [14,15,16,17,18]:
        schedule[f"201910{day:02d}"] = ["45"]

    # 川崎: 21,22,23,24,25,26日
    for day in [21,22,23,24,25,26]:
        schedule[f"201910{day:02d}"] = ["43"]

    # 船橋: 28,29,30,31日
    for day in [28,29,30,31]:
        schedule[f"201910{day:02d}"] = ["44"]

    return schedule

# 2019年11月のデータ
def process_2019_11():
    """2019年11月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1日
    schedule[f"20191101"] = ["44"]

    # 浦和: 7,8,9,10,11,12,13,14,15,16日（7日,15日はDirt）
    for day in [7,8,9,10,11,12,13,14,15,16]:
        schedule[f"201911{day:02d}"] = ["45"]

    # 大井: 16,17,18,19,20日
    for day in [16,17,18,19,20]:
        schedule[f"201911{day:02d}"] = ["42"]

    # 川崎: 21,22,23,24,25,26日
    for day in [21,22,23,24,25,26]:
        schedule[f"201911{day:02d}"] = ["43"]

    return schedule

# 2019年12月のデータ
def process_2019_12():
    """2019年12月のスケジュールデータ"""
    schedule = {}

    # 大井: 2,3,4,5,6,7,8,9,10日（10日はDirt）、27,28日
    for day in [2,3,4,5,6,7,8,9,10,27,28]:
        schedule[f"201912{day:02d}"] = ["42"]

    # 船橋: 14,15,16,17,18日（16日はDirt）
    for day in [14,15,16,17,18]:
        schedule[f"201912{day:02d}"] = ["44"]

    # 川崎: 21,22,23,24,25日（23日はDirt）
    for day in [21,22,23,24,25]:
        schedule[f"201912{day:02d}"] = ["43"]

    # 浦和: 25,26,27日
    for day in [25,26,27]:
        schedule[f"201912{day:02d}"] = ["45"]

    return schedule

if __name__ == "__main__":
    master_file = "/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json"

    print("="*60)
    print("2019年スケジュールマスター更新開始")
    print("="*60)

    # 2019年1月を追加
    jan_2019 = process_2019_01()
    add_year_schedule(master_file, jan_2019, "2019年1月")

    # 2019年2月を追加
    feb_2019 = process_2019_02()
    add_year_schedule(master_file, feb_2019, "2019年2月")

    # 2019年3月を追加
    mar_2019 = process_2019_03()
    add_year_schedule(master_file, mar_2019, "2019年3月")

    # 2019年4月を追加
    apr_2019 = process_2019_04()
    add_year_schedule(master_file, apr_2019, "2019年4月")

    # 2019年5月を追加
    may_2019 = process_2019_05()
    add_year_schedule(master_file, may_2019, "2019年5月")

    # 2019年6月を追加
    jun_2019 = process_2019_06()
    add_year_schedule(master_file, jun_2019, "2019年6月")

    # 2019年7月を追加
    jul_2019 = process_2019_07()
    add_year_schedule(master_file, jul_2019, "2019年7月")

    # 2019年8月を追加
    aug_2019 = process_2019_08()
    add_year_schedule(master_file, aug_2019, "2019年8月")

    # 2019年9月を追加
    sep_2019 = process_2019_09()
    add_year_schedule(master_file, sep_2019, "2019年9月")

    # 2019年10月を追加
    oct_2019 = process_2019_10()
    add_year_schedule(master_file, oct_2019, "2019年10月")

    # 2019年11月を追加
    nov_2019 = process_2019_11()
    add_year_schedule(master_file, nov_2019, "2019年11月")

    # 2019年12月を追加
    dec_2019 = process_2019_12()
    add_year_schedule(master_file, dec_2019, "2019年12月")

    print("\n✅ 2019年のスケジュール追加が完了しました！")