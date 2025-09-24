#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2020年のスケジュールをマスターファイルに追加
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

# 2020年1月のデータ
def process_2020_01():
    """2020年1月のスケジュールデータ"""
    schedule = {}

    # 川崎: 1,2,3,4,5,6日、8,9,10日（7日はDirt）
    for day in [1,2,3,4,5,6,8,9,10]:
        schedule[f"202001{day:02d}"] = ["43"]

    # 船橋: 13,14,15,16,17日
    for day in [13,14,15,16,17]:
        schedule[f"202001{day:02d}"] = ["44"]

    # 浦和: 15,16,17,18日
    for day in [15,16,17,18]:
        schedule[f"202001{day:02d}"] = ["45"]

    # 大井: 27,28,29,30,31日（29日はDirt）
    for day in [27,28,29,30,31]:
        schedule[f"202001{day:02d}"] = ["42"]

    return schedule

# 2020年2月のデータ
def process_2020_02():
    """2020年2月のスケジュールデータ"""
    schedule = {}

    # 大井: 3,4,5,6,7日、10,11,12,13,14日
    for day in [3,4,5,6,7,10,11,12,13,14]:
        schedule[f"202002{day:02d}"] = ["42"]

    # 船橋: 17,18,19,20,21日
    for day in [17,18,19,20,21]:
        schedule[f"202002{day:02d}"] = ["44"]

    # 浦和: 24,25,26,27,28日
    for day in [24,25,26,27,28]:
        schedule[f"202002{day:02d}"] = ["45"]

    return schedule

# 2020年3月のデータ
def process_2020_03():
    """2020年3月のスケジュールデータ"""
    schedule = {}

    # 川崎: 2,3,4,5,6日（5日はDirt）
    for day in [2,3,4,5,6]:
        schedule[f"202003{day:02d}"] = ["43"]

    # 船橋: 16,17日、19,20,21,22,23日（17日はDirt）
    for day in [16,17,19,20,21,22,23]:
        schedule[f"202003{day:02d}"] = ["44"]

    # 大井: 23,24,25,26,27日
    for day in [23,24,25,26,27]:
        schedule[f"202003{day:02d}"] = ["42"]

    # 浦和: 23,24,25,26,27日
    for day in [23,24,25,26,27]:
        schedule[f"202003{day:02d}"] = ["45"]

    return schedule

# 2020年4月のデータ
def process_2020_04():
    """2020年4月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3日（2日はDirt）
    for day in [1,2,3]:
        schedule[f"202004{day:02d}"] = ["44"]

    # 大井: 13,14,15日（15日はDirt）、17,18,19,20,21日
    for day in [13,14,15,17,18,19,20,21]:
        schedule[f"202004{day:02d}"] = ["42"]

    # 川崎: 20,21,22,23,24日
    for day in [20,21,22,23,24]:
        schedule[f"202004{day:02d}"] = ["43"]

    # 浦和: 27,28,29,30日
    for day in [27,28,29,30]:
        schedule[f"202004{day:02d}"] = ["45"]

    return schedule

# 2020年5月のデータ
def process_2020_05():
    """2020年5月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1日
    schedule[f"20200501"] = ["45"]

    # 大井: 1,2日、5,6,7,8日
    for day in [1,2,5,6,7,8]:
        schedule[f"202005{day:02d}"] = ["42"]

    # 船橋: 4日、6日、11,12日（5日はDirt）
    for day in [4,5,6,11,12]:
        schedule[f"202005{day:02d}"] = ["44"]

    # 川崎: 18,19,20,21,22日
    for day in [18,19,20,21,22]:
        schedule[f"202005{day:02d}"] = ["43"]

    # 浦和: 25,26,27,28,29日（27日はDirt）
    for day in [25,26,27,28,29]:
        schedule[f"202005{day:02d}"] = ["45"]

    return schedule

# 2020年6月のデータ
def process_2020_06():
    """2020年6月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4,5日、8,9,10日（9日はDirt）
    for day in [1,2,3,4,5,8,9,10]:
        schedule[f"202006{day:02d}"] = ["42"]

    # 川崎: 15,16,17,18,19日（17日はDirt）
    for day in [15,16,17,18,19]:
        schedule[f"202006{day:02d}"] = ["43"]

    # 船橋: 22,23,24,25,26日
    for day in [22,23,24,25,26]:
        schedule[f"202006{day:02d}"] = ["44"]

    # 浦和: 29,30日
    for day in [29,30]:
        schedule[f"202006{day:02d}"] = ["45"]

    return schedule

# 2020年7月のデータ
def process_2020_07():
    """2020年7月のスケジュールデータ"""
    schedule = {}

    # 浦和: 1,2,3,4,5,6日
    for day in [1,2,3,4,5,6]:
        schedule[f"202007{day:02d}"] = ["45"]

    # 大井: 13,14,15日（15日はDirt）、17日
    for day in [13,14,15,17]:
        schedule[f"202007{day:02d}"] = ["42"]

    # 川崎: 20,21,22,23,24日（22日はDirt）
    for day in [20,21,22,23,24]:
        schedule[f"202007{day:02d}"] = ["43"]

    # 船橋: 27,28,29,30,31日
    for day in [27,28,29,30,31]:
        schedule[f"202007{day:02d}"] = ["44"]

    return schedule

# 2020年8月のデータ
def process_2020_08():
    """2020年8月のスケジュールデータ"""
    schedule = {}

    # 大井: 1,2,3,4,5,6,7日
    for day in [1,2,3,4,5,6,7]:
        schedule[f"202008{day:02d}"] = ["42"]

    # 船橋: 3,4,5,6,7日
    for day in [3,4,5,6,7]:
        schedule[f"202008{day:02d}"] = ["44"]

    # 川崎: 10,11,12,13,14日、17,18,19,20,21日
    for day in [10,11,12,13,14,17,18,19,20,21]:
        schedule[f"202008{day:02d}"] = ["43"]

    # 浦和: 17,18,19,20日
    for day in [17,18,19,20]:
        schedule[f"202008{day:02d}"] = ["45"]

    return schedule

# 2020年9月のデータ
def process_2020_09():
    """2020年9月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3,4日、28,29,30日（29日はDirt）
    for day in [1,2,3,4,28,29,30]:
        schedule[f"202009{day:02d}"] = ["44"]

    # 川崎: 1,2,3,4日、7,8日
    for day in [1,2,3,4,7,8]:
        schedule[f"202009{day:02d}"] = ["43"]

    # 大井: 14,15,16,17,18日、21,22,23,24,25日
    for day in [14,15,16,17,18,21,22,23,24,25]:
        schedule[f"202009{day:02d}"] = ["42"]

    # 浦和: 22,23,24,25日（23日はDirt）
    for day in [22,23,24,25]:
        schedule[f"202009{day:02d}"] = ["45"]

    return schedule

# 2020年10月のデータ
def process_2020_10():
    """2020年10月のスケジュールデータ"""
    schedule = {}

    # 船橋: 12,13,14,15,16,17,18日
    for day in [12,13,14,15,16,17,18]:
        schedule[f"202010{day:02d}"] = ["44"]

    # 大井: 5,6,7,8,9日（7,8日はDirt）
    for day in [5,6,7,8,9]:
        schedule[f"202010{day:02d}"] = ["42"]

    # 川崎: 19,20,21,22,23,24日
    for day in [19,20,21,22,23,24]:
        schedule[f"202010{day:02d}"] = ["43"]

    # 浦和: 26,27,28,29,30日
    for day in [26,27,28,29,30]:
        schedule[f"202010{day:02d}"] = ["45"]

    return schedule

# 2020年11月のデータ
def process_2020_11():
    """2020年11月のスケジュールデータ"""
    schedule = {}

    # 大井: 2,3,4,5,6日（4日はDirt）、9,10,11,12,13日
    for day in [2,3,4,5,6,9,10,11,12,13]:
        schedule[f"202011{day:02d}"] = ["42"]

    # 川崎: 16,17,18,19,20日
    for day in [16,17,18,19,20]:
        schedule[f"202011{day:02d}"] = ["43"]

    # 浦和: 23,24,25,26日（23日はDirt）
    for day in [23,24,25,26]:
        schedule[f"202011{day:02d}"] = ["45"]

    # 船橋: 30日
    schedule[f"20201130"] = ["44"]

    return schedule

# 2020年12月のデータ
def process_2020_12():
    """2020年12月のスケジュールデータ"""
    schedule = {}

    # 船橋: 1,2,3,4日（3日はDirt）
    for day in [1,2,3,4]:
        schedule[f"202012{day:02d}"] = ["44"]

    # 大井: 14,15,16,17,18,19,20日（20日はDirt）、28,29日
    for day in [14,15,16,17,18,19,20,28,29]:
        schedule[f"202012{day:02d}"] = ["42"]

    # 川崎: 21,22,23,24,25日（23日はDirt）
    for day in [21,22,23,24,25]:
        schedule[f"202012{day:02d}"] = ["43"]

    # 浦和: 21,22,23,24,25日
    for day in [21,22,23,24,25]:
        schedule[f"202012{day:02d}"] = ["45"]

    return schedule

if __name__ == "__main__":
    master_file = "/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json"

    print("="*60)
    print("2020年スケジュールマスター更新開始")
    print("="*60)

    # 2020年1月を追加
    jan_2020 = process_2020_01()
    add_year_schedule(master_file, jan_2020, "2020年1月")

    # 2020年2月を追加
    feb_2020 = process_2020_02()
    add_year_schedule(master_file, feb_2020, "2020年2月")

    # 2020年3月を追加
    mar_2020 = process_2020_03()
    add_year_schedule(master_file, mar_2020, "2020年3月")

    # 2020年4月を追加
    apr_2020 = process_2020_04()
    add_year_schedule(master_file, apr_2020, "2020年4月")

    # 2020年5月を追加
    may_2020 = process_2020_05()
    add_year_schedule(master_file, may_2020, "2020年5月")

    # 2020年6月を追加
    jun_2020 = process_2020_06()
    add_year_schedule(master_file, jun_2020, "2020年6月")

    # 2020年7月を追加
    jul_2020 = process_2020_07()
    add_year_schedule(master_file, jul_2020, "2020年7月")

    # 2020年8月を追加
    aug_2020 = process_2020_08()
    add_year_schedule(master_file, aug_2020, "2020年8月")

    # 2020年9月を追加
    sep_2020 = process_2020_09()
    add_year_schedule(master_file, sep_2020, "2020年9月")

    # 2020年10月を追加
    oct_2020 = process_2020_10()
    add_year_schedule(master_file, oct_2020, "2020年10月")

    # 2020年11月を追加
    nov_2020 = process_2020_11()
    add_year_schedule(master_file, nov_2020, "2020年11月")

    # 2020年12月を追加
    dec_2020 = process_2020_12()
    add_year_schedule(master_file, dec_2020, "2020年12月")

    print("\n✅ 2020年のスケジュール追加が完了しました！")