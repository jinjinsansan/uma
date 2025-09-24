#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2021年のスケジュールをマスターファイルに追加
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

# 2021年1月のデータ
def process_2021_01():
    """2021年1月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5,6日、8,9,10日（7日はDirt）
    for day in [1,2,3,4,5,6,8,9,10]:
        schedule[f"202101{day:02d}"] = ["43"]

    # 浦和: 11,12,13日
    for day in [11,12,13]:
        schedule[f"202101{day:02d}"] = ["45"]

    # 船橋: 18,19,20,21,22日
    for day in [18,19,20,21,22]:
        schedule[f"202101{day:02d}"] = ["44"]

    # 大井: 25,26,27,28,29日（27日はDirt）
    for day in [25,26,27,28,29]:
        schedule[f"202101{day:02d}"] = ["42"]

    return schedule

# 2021年2月のデータ
def process_2021_02():
    """2021年2月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5日、8,9,10,11日
    for day in [1,2,3,4,5,8,9,10,11]:
        schedule[f"202102{day:02d}"] = ["45"]

    # 船橋: 15,16,17,18,19日
    for day in [15,16,17,18,19]:
        schedule[f"202102{day:02d}"] = ["44"]

    # 大井: 22,23,24,25,26日
    for day in [22,23,24,25,26]:
        schedule[f"202102{day:02d}"] = ["42"]

    return schedule

# 2021年3月のデータ
def process_2021_03():
    """2021年3月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5日（4日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202103{day:02d}"] = ["43"]

    # 大井: 8,9,10,11,12日、15,16,17,18,19日
    for day in [8,9,10,11,12,15,16,17,18,19]:
        schedule[f"202103{day:02d}"] = ["42"]

    # 船橋: 15,16,17,18,19日（17日はDirt）
    for day in [15,16,17,18,19]:
        schedule[f"202103{day:02d}"] = ["44"]

    # 浦和: 29,30,31日
    for day in [29,30,31]:
        schedule[f"202103{day:02d}"] = ["45"]

    return schedule

# 2021年4月のデータ
def process_2021_04():
    """2021年4月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2日
    for day in [1,2]:
        schedule[f"202104{day:02d}"] = ["45"]

    # 船橋: 5,6,7,8,9日（7日はDirt）
    for day in [5,6,7,8,9]:
        schedule[f"202104{day:02d}"] = ["44"]

    # 大井: 12,13,14,15,16日（14日はDirt）、19,20,21,22,23日
    for day in [12,13,14,15,16,19,20,21,22,23]:
        schedule[f"202104{day:02d}"] = ["42"]

    # 川崎: 26,27,28,29,30日
    for day in [26,27,28,29,30]:
        schedule[f"202104{day:02d}"] = ["43"]

    return schedule

# 2021年5月のデータ
def process_2021_05():
    """2021年5月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2日、5,6,7日
    for day in [1,2,5,6,7]:
        schedule[f"202105{day:02d}"] = ["42"]

    # 船橋: 3,4日、6,7日（5日はDirt）
    for day in [3,4,6,7]:
        schedule[f"202105{day:02d}"] = ["44"]

    # 浦和: 17,18,19,20,21,22日
    for day in [17,18,19,20,21,22]:
        schedule[f"202105{day:02d}"] = ["45"]

    # 川崎: 24,25,26,27,28日
    for day in [24,25,26,27,28]:
        schedule[f"202105{day:02d}"] = ["43"]

    return schedule

# 2021年6月のデータ
def process_2021_06():
    """2021年6月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5日（3日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202106{day:02d}"] = ["45"]

    # 大井: 7,8,9日、11,12日、14,15日（15日はDirt）
    for day in [7,8,9,11,12,14,15]:
        schedule[f"202106{day:02d}"] = ["42"]

    # 川崎: 16,17,18,19,20日（18日はDirt）
    for day in [16,17,18,19,20]:
        schedule[f"202106{day:02d}"] = ["43"]

    # 船橋: 21,22,23,24,25日
    for day in [21,22,23,24,25]:
        schedule[f"202106{day:02d}"] = ["44"]

    return schedule

# 2021年7月のデータ
def process_2021_07():
    """2021年7月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5,6日
    for day in [1,2,3,4,5,6]:
        schedule[f"202107{day:02d}"] = ["45"]

    # 大井: 1,2,3,4,5日（5日はDirt）、7,8日
    for day in [1,2,3,4,5,7,8]:
        schedule[f"202107{day:02d}"] = ["42"]

    # 川崎: 9,10,11,12,13日（12日はDirt）、15,16,17,18,19日
    for day in [9,10,11,12,13,15,16,17,18,19]:
        schedule[f"202107{day:02d}"] = ["43"]

    # 船橋: 20,21,22,23,24日
    for day in [20,21,22,23,24]:
        schedule[f"202107{day:02d}"] = ["44"]

    return schedule

# 2021年8月のデータ
def process_2021_08():
    """2021年8月のスケジュールデータ"""
    schedule = {}

    # 大井: 2,3,4,5,6日、9,10,11,12,13日
    for day in [2,3,4,5,6,9,10,11,12,13]:
        schedule[f"202108{day:02d}"] = ["42"]

    # 船橋: 16,17,18,19,20日
    for day in [16,17,18,19,20]:
        schedule[f"202108{day:02d}"] = ["44"]

    # 浦和: 23,24,25,26日
    for day in [23,24,25,26]:
        schedule[f"202108{day:02d}"] = ["45"]

    # 川崎: 30,31日
    for day in [30,31]:
        schedule[f"202108{day:02d}"] = ["43"]

    return schedule

# 2021年9月のデータ
def process_2021_09():
    """2021年9月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3日、20,21,22,23,24日
    for day in [1,2,3,20,21,22,23,24]:
        schedule[f"202109{day:02d}"] = ["43"]

    # 船橋: 1,2,3日、6,7,8日（7日はDirt）
    for day in [1,2,3,6,7,8]:
        schedule[f"202109{day:02d}"] = ["44"]

    # 大井: 13,14,15,16,17日、20,21,22,23,24日
    for day in [13,14,15,16,17,20,21,22,23,24]:
        schedule[f"202109{day:02d}"] = ["42"]

    # 浦和: 27,28,29,30日（29日はDirt）
    for day in [27,28,29,30]:
        schedule[f"202109{day:02d}"] = ["45"]

    return schedule

# 2021年10月のデータ
def process_2021_10():
    """2021年10月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3,4,5,6,7日
    for day in [1,2,3,4,5,6,7]:
        schedule[f"202110{day:02d}"] = ["44"]

    # 大井: 4,5,6,8日（5,6日はDirt）
    for day in [4,5,6,8]:
        schedule[f"202110{day:02d}"] = ["42"]

    # 川崎: 18,19,20,21,22日
    for day in [18,19,20,21,22]:
        schedule[f"202110{day:02d}"] = ["43"]

    # 浦和: 25,26,27,28,29日
    for day in [25,26,27,28,29]:
        schedule[f"202110{day:02d}"] = ["45"]

    return schedule

# 2021年11月のデータ
def process_2021_11():
    """2021年11月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4,5日、8,9,10,11,12日
    for day in [1,2,3,4,5,8,9,10,11,12]:
        schedule[f"202111{day:02d}"] = ["42"]

    # 川崎: 15,16,17,18,19日
    for day in [15,16,17,18,19]:
        schedule[f"202111{day:02d}"] = ["43"]

    # 浦和: 22,23,24,25,26日（23日はDirt）
    for day in [22,23,24,25,26]:
        schedule[f"202111{day:02d}"] = ["45"]

    # 船橋: 29,30日
    for day in [29,30]:
        schedule[f"202111{day:02d}"] = ["44"]

    return schedule

# 2021年12月のデータ
def process_2021_12():
    """2021年12月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3日（1日はDirt）
    for day in [1,2,3]:
        schedule[f"202112{day:02d}"] = ["44"]

    # 大井: 13,14,15,16,17日、20日（20日はDirt）、29,30,31日
    for day in [13,14,15,16,17,20,29,30,31]:
        schedule[f"202112{day:02d}"] = ["42"]

    # 川崎: 21,22,23,24,25日（23日はDirt）
    for day in [21,22,23,24,25]:
        schedule[f"202112{day:02d}"] = ["43"]

    # 浦和: 27,28,29,30,31日
    for day in [27,28,29,30,31]:
        schedule[f"202112{day:02d}"] = ["45"]

    return schedule

if __name__ == "__main__":
    master_file = "/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json"

    print("="*60)
    print("2021年スケジュールマスター更新開始")
    print("="*60)

    # 2021年1月を追加
    jan_2021 = process_2021_01()
    add_year_schedule(master_file, jan_2021, "2021年1月")

    # 2021年2月を追加
    feb_2021 = process_2021_02()
    add_year_schedule(master_file, feb_2021, "2021年2月")

    # 2021年3月を追加
    mar_2021 = process_2021_03()
    add_year_schedule(master_file, mar_2021, "2021年3月")

    # 2021年4月を追加
    apr_2021 = process_2021_04()
    add_year_schedule(master_file, apr_2021, "2021年4月")

    # 2021年5月を追加
    may_2021 = process_2021_05()
    add_year_schedule(master_file, may_2021, "2021年5月")

    # 2021年6月を追加
    jun_2021 = process_2021_06()
    add_year_schedule(master_file, jun_2021, "2021年6月")

    # 2021年7月を追加
    jul_2021 = process_2021_07()
    add_year_schedule(master_file, jul_2021, "2021年7月")

    # 2021年8月を追加
    aug_2021 = process_2021_08()
    add_year_schedule(master_file, aug_2021, "2021年8月")

    # 2021年9月を追加
    sep_2021 = process_2021_09()
    add_year_schedule(master_file, sep_2021, "2021年9月")

    # 2021年10月を追加
    oct_2021 = process_2021_10()
    add_year_schedule(master_file, oct_2021, "2021年10月")

    # 2021年11月を追加
    nov_2021 = process_2021_11()
    add_year_schedule(master_file, nov_2021, "2021年11月")

    # 2021年12月を追加
    dec_2021 = process_2021_12()
    add_year_schedule(master_file, dec_2021, "2021年12月")

    print("\n✅ 2021年のスケジュール追加が完了しました！")