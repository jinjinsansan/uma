#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騎手データベース構造調査スクリプト
安全に騎手関連データを確認
"""

import psycopg2
import json
from datetime import datetime

# データベース接続パラメータ（馬版と同じ）
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "PC-KEIBA",
    "user": "postgres",
    "password": "postgres"
}

def check_jockey_columns():
    """騎手関連カラムの確認"""
    try:
        # client_encodingを明示的に設定
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        conn.set_client_encoding('SJIS')  # PC-KEIBAはSJISの可能性
        cur = conn.cursor()

        print("=" * 60)
        print("騎手関連カラム調査")
        print("=" * 60)

        # nvd_seテーブルの騎手関連カラム確認
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'nvd_se'
            AND column_name LIKE '%kishu%'
            ORDER BY column_name
        """)

        print("\n📋 nvd_seテーブルの騎手関連カラム:")
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")

        # サンプルデータ確認
        cur.execute("""
            SELECT
                kishumei_ryakusho,
                COUNT(*) as race_count
            FROM nvd_se
            WHERE kaisai_nen = '2024'
                AND keibajo_code IN ('42','43','44','45')
                AND kishumei_ryakusho IS NOT NULL
                AND kishumei_ryakusho != ''
            GROUP BY kishumei_ryakusho
            ORDER BY race_count DESC
            LIMIT 10
        """)

        print("\n📊 2024年の騎手別騎乗数（上位10名）:")
        jockeys = cur.fetchall()
        for jockey in jockeys:
            print(f"  - {jockey[0]}: {jockey[1]}騎乗")

        # データ範囲確認
        cur.execute("""
            SELECT
                kaisai_nen,
                COUNT(DISTINCT kishumei_ryakusho) as jockey_count,
                COUNT(*) as race_count
            FROM nvd_se
            WHERE kaisai_nen BETWEEN '2019' AND '2025'
                AND keibajo_code IN ('42','43','44','45')
                AND kishumei_ryakusho IS NOT NULL
                AND kishumei_ryakusho != ''
            GROUP BY kaisai_nen
            ORDER BY kaisai_nen
        """)

        print("\n📅 年度別データ量:")
        years = cur.fetchall()
        for year in years:
            print(f"  {year[0]}年: {year[1]}名, {year[2]}騎乗")

        # 必要なテーブルの結合テスト
        cur.execute("""
            SELECT COUNT(*)
            FROM nvd_se se
            JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
            LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
                AND se.keibajo_code IN ('42','43','44','45')
            LIMIT 1
        """)

        result = cur.fetchone()
        print(f"\n✅ テーブル結合テスト: {result[0]}件（正常）")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def check_sample_data():
    """サンプルデータの詳細確認"""
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        conn.set_client_encoding('SJIS')  # PC-KEIBAはSJISの可能性
        cur = conn.cursor()

        print("\n" + "=" * 60)
        print("サンプルデータ詳細確認")
        print("=" * 60)

        # 1レコードの全データ確認
        cur.execute("""
            SELECT
                se.kishumei_ryakusho,
                se.kaisai_nen || se.kaisai_tsukihi as race_date,
                se.keibajo_code,
                ra.kyori,
                ra.track_code,
                ra.babajotai_code_shiba,
                ra.babajotai_code_dirt,
                ra.racenamef,
                se.wakuban,
                se.bamei,
                se.kakutei_chakujun,
                ra.shusso_tosu,
                um.ketto_joho_01b as sire
            FROM nvd_se se
            JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
            LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
                AND se.keibajo_code IN ('42','43','44','45')
                AND se.kishumei_ryakusho IS NOT NULL
                AND se.kishumei_ryakusho != ''
                AND se.kakutei_chakujun IS NOT NULL
                AND se.kakutei_chakujun != '00'
            LIMIT 1
        """)

        sample = cur.fetchone()
        if sample:
            print("\n📝 サンプルレコード:")
            fields = [
                "騎手名", "レース日", "会場コード", "距離", "トラック",
                "芝馬場", "ダート馬場", "レース名", "枠番", "馬名",
                "着順", "頭数", "種牡馬"
            ]
            for i, field in enumerate(fields):
                print(f"  {field}: {sample[i]}")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    print("🏇 地方競馬騎手データベース調査")
    print(f"実行時刻: {datetime.now()}")

    # カラム確認
    if check_jockey_columns():
        print("\n✅ カラム確認完了")

    # サンプルデータ確認
    if check_sample_data():
        print("\n✅ サンプルデータ確認完了")

    print("\n調査完了！")