#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スケジュールマスター更新スクリプト
既存のマスターファイルに新しい年のスケジュールを追加
"""

import json
import os
from datetime import datetime

def add_year_schedule(master_file, year_data, year):
    """
    年度のスケジュールをマスターファイルに追加

    Args:
        master_file: マスターファイルのパス
        year_data: 追加する年のスケジュールデータ
        year: 対象年（例: 2023）
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

    print(f"✅ {year}年のスケジュール追加完了")
    print(f"   追加日数: {added_count}日")
    print(f"   総日数: {master['metadata']['total_days']}日")
    print(f"   期間: {master['metadata']['period']}")

    return master

# 2023年1月のデータを処理
def process_2023_01():
    """2023年1月のスケジュールデータ"""
    schedule = {}

    # 川崎: 2,3,4,5,6,7,8日
    for day in [2,3,4,5,6,7,8]:
        schedule[f"202301{day:02d}"] = ["43"]

    # 浦和: 16,17,18,19日
    for day in [16,17,18,19]:
        schedule[f"202301{day:02d}"] = ["45"]

    # 船橋: 23,24,25,26,27日
    for day in [23,24,25,26,27]:
        schedule[f"202301{day:02d}"] = ["44"]

    # 大井: 28,29,30,31日（30日はDirt）
    for day in [28,29,30,31]:
        schedule[f"202301{day:02d}"] = ["42"]

    return schedule

# 2023年2月のデータを処理
def process_2023_02():
    """2023年2月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5日（1日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202302{day:02d}"] = ["43"]

    # 船橋: 6,7,8,9,10日
    for day in [6,7,8,9,10]:
        schedule[f"202302{day:02d}"] = ["44"]

    # 浦和: 13,14,15,16,17日
    for day in [13,14,15,16,17]:
        schedule[f"202302{day:02d}"] = ["45"]

    # 大井: 20,21,22,23,24日
    for day in [20,21,22,23,24]:
        schedule[f"202302{day:02d}"] = ["42"]

    return schedule

# 2023年3月のデータを処理
def process_2023_03():
    """2023年3月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3日（1日はDirt）
    for day in [1,2,3]:
        schedule[f"202303{day:02d}"] = ["43"]

    # 大井: 6,7,8,9,10日
    for day in [6,7,8,9,10]:
        schedule[f"202303{day:02d}"] = ["42"]

    # 船橋: 13,14,15,16,17日（15日はDirt）
    for day in [13,14,15,16,17]:
        schedule[f"202303{day:02d}"] = ["44"]

    # 浦和: 20,21,22,23,24日
    for day in [20,21,22,23,24]:
        schedule[f"202303{day:02d}"] = ["45"]

    return schedule

# 2023年4月のデータを処理
def process_2023_04():
    """2023年4月のスケジュールデータ"""
    schedule = {}

    # 川崎: 3,4,5,6,7日
    for day in [3,4,5,6,7]:
        schedule[f"202304{day:02d}"] = ["43"]

    # 船橋: 10,11,12,13,14日（12日はDirt）
    for day in [10,11,12,13,14]:
        schedule[f"202304{day:02d}"] = ["44"]

    # 大井: 17,18,19,20,21日（19日はDirt）
    for day in [17,18,19,20,21]:
        schedule[f"202304{day:02d}"] = ["42"]

    # 浦和: 24,25,26,27,28日
    for day in [24,25,26,27,28]:
        schedule[f"202304{day:02d}"] = ["45"]

    return schedule

# 2023年5月のデータを処理
def process_2023_05():
    """2023年5月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3,4,5日（4日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202305{day:02d}"] = ["44"]

    # 大井: 8,9,10,11,12日
    for day in [8,9,10,11,12]:
        schedule[f"202305{day:02d}"] = ["42"]

    # 川崎: 15,16,17,18,19日
    for day in [15,16,17,18,19]:
        schedule[f"202305{day:02d}"] = ["43"]

    # 浦和: 29,30,31日（31日はDirt）
    for day in [29,30,31]:
        schedule[f"202305{day:02d}"] = ["45"]

    return schedule

# 2023年6月のデータを処理
def process_2023_06():
    """2023年6月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5,6日
    for day in [1,2,3,4,5,6]:
        schedule[f"202306{day:02d}"] = ["45"]

    # 大井: 9,10,11,12,13日（13日はDirt）
    for day in [9,10,11,12,13]:
        schedule[f"202306{day:02d}"] = ["42"]

    # 川崎: 14,15,16,17,18日（16日はDirt）
    for day in [14,15,16,17,18]:
        schedule[f"202306{day:02d}"] = ["43"]

    # 船橋: 19,20,21,22,23日
    for day in [19,20,21,22,23]:
        schedule[f"202306{day:02d}"] = ["44"]

    return schedule

# 2023年7月のデータを処理
def process_2023_07():
    """2023年7月のスケジュールデータ"""
    schedule = {}

    # 川崎: 3,4,5,6,7日（5日はDirt）
    for day in [3,4,5,6,7]:
        schedule[f"202307{day:02d}"] = ["43"]

    # 大井: 10,11,12,13,14日（12日はDirt）
    for day in [10,11,12,13,14]:
        schedule[f"202307{day:02d}"] = ["42"]

    # 浦和: 17,18,19,20日
    for day in [17,18,19,20]:
        schedule[f"202307{day:02d}"] = ["45"]

    # 船橋: 24,25,26,27,28日
    for day in [24,25,26,27,28]:
        schedule[f"202307{day:02d}"] = ["44"]

    return schedule

# 2023年8月のデータを処理
def process_2023_08():
    """2023年8月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4日
    for day in [1,2,3,4]:
        schedule[f"202308{day:02d}"] = ["42"]

    # 船橋: 7,8,9,10,11日
    for day in [7,8,9,10,11]:
        schedule[f"202308{day:02d}"] = ["44"]

    # 浦和: 14,15,16,17,18,19,20,21日
    for day in [14,15,16,17,18,19,20,21]:
        schedule[f"202308{day:02d}"] = ["45"]

    # 川崎: 22,23,24,25,26日
    for day in [22,23,24,25,26]:
        schedule[f"202308{day:02d}"] = ["43"]

    return schedule

# 2023年9月のデータを処理
def process_2023_09():
    """2023年9月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5日（3日はDirt）
    for day in [1,2,3,4,5]:
        schedule[f"202309{day:02d}"] = ["45"]

    # 大井: 6,7,8,9,10日
    for day in [6,7,8,9,10]:
        schedule[f"202309{day:02d}"] = ["42"]

    # 川崎: 11,12,13,14,15日
    for day in [11,12,13,14,15]:
        schedule[f"202309{day:02d}"] = ["43"]

    # 船橋: 25,26,27,28,29日（27日はDirt）
    for day in [25,26,27,28,29]:
        schedule[f"202309{day:02d}"] = ["44"]

    return schedule

# 2023年10月のデータを処理
def process_2023_10():
    """2023年10月のスケジュールデータ"""
    schedule = {}

    # 大井: 2,3,4,5,6日（4,5日はDirt）
    for day in [2,3,4,5,6]:
        schedule[f"202310{day:02d}"] = ["42"]

    # 川崎: 9,10,11,12,13日
    for day in [9,10,11,12,13]:
        schedule[f"202310{day:02d}"] = ["43"]

    # 浦和: 16,17,18,19,20日
    for day in [16,17,18,19,20]:
        schedule[f"202310{day:02d}"] = ["45"]

    # 船橋: 23,24,25,26,27日
    for day in [23,24,25,26,27]:
        schedule[f"202310{day:02d}"] = ["44"]

    return schedule

# 2023年11月のデータを処理
def process_2023_11():
    """2023年11月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4日（3日はDirt）
    for day in [1,2,3,4]:
        schedule[f"202311{day:02d}"] = ["42"]

    # 川崎: 6,7,8,9,10日
    for day in [6,7,8,9,10]:
        schedule[f"202311{day:02d}"] = ["43"]

    # 浦和: 20,21,22,23,24日（23日はDirt）
    for day in [20,21,22,23,24]:
        schedule[f"202311{day:02d}"] = ["45"]

    # 船橋: 27,28,29,30日（29日はDirt）
    for day in [27,28,29,30]:
        schedule[f"202311{day:02d}"] = ["44"]

    return schedule

# 2023年12月のデータを処理
def process_2023_12():
    """2023年12月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2日
    for day in [1,2]:
        schedule[f"202312{day:02d}"] = ["44"]

    # 大井: 4,5,6,7,8,11,12,13,14日（14日はDirt）、29,30,31日
    for day in [4,5,6,7,8,11,12,13,14]:
        schedule[f"202312{day:02d}"] = ["42"]
    for day in [29,30,31]:
        schedule[f"202312{day:02d}"] = ["42"]

    # 川崎: 18,19,20,21,22日（20日はDirt）
    for day in [18,19,20,21,22]:
        schedule[f"202312{day:02d}"] = ["43"]

    # 浦和: 25,26,27,28日
    for day in [25,26,27,28]:
        schedule[f"202312{day:02d}"] = ["45"]

    return schedule

if __name__ == "__main__":
    master_file = "/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json"

    print("="*60)
    print("スケジュールマスター更新開始")
    print("="*60)

    # 2023年1月を追加
    jan_2023 = process_2023_01()
    add_year_schedule(master_file, jan_2023, "2023年1月")

    # 2023年2月を追加
    feb_2023 = process_2023_02()
    add_year_schedule(master_file, feb_2023, "2023年2月")

    # 2023年3月を追加
    mar_2023 = process_2023_03()
    add_year_schedule(master_file, mar_2023, "2023年3月")

    # 2023年4月を追加
    apr_2023 = process_2023_04()
    add_year_schedule(master_file, apr_2023, "2023年4月")

    # 2023年5月を追加
    may_2023 = process_2023_05()
    add_year_schedule(master_file, may_2023, "2023年5月")

    # 2023年6月を追加
    jun_2023 = process_2023_06()
    add_year_schedule(master_file, jun_2023, "2023年6月")

    # 2023年7月を追加
    jul_2023 = process_2023_07()
    add_year_schedule(master_file, jul_2023, "2023年7月")

    # 2023年8月を追加
    aug_2023 = process_2023_08()
    add_year_schedule(master_file, aug_2023, "2023年8月")

    # 2023年9月を追加
    sep_2023 = process_2023_09()
    add_year_schedule(master_file, sep_2023, "2023年9月")

    # 2023年10月を追加
    oct_2023 = process_2023_10()
    add_year_schedule(master_file, oct_2023, "2023年10月")

    # 2023年11月を追加
    nov_2023 = process_2023_11()
    add_year_schedule(master_file, nov_2023, "2023年11月")

    # 2023年12月を追加
    dec_2023 = process_2023_12()
    add_year_schedule(master_file, dec_2023, "2023年12月")

    print("\n✅ 2023年完了！次は2022年のデータをお待ちしています...")