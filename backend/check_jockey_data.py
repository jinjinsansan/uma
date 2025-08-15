import mysql.connector

connection = mysql.connector.connect(
    host='172.25.160.1',
    database='mykeibadb',
    user='root',
    password='04050405Aoi-',
    port=3306,
    charset='utf8mb4'
)

cursor = connection.cursor()

# サンプルデータを取得
print("=== サンプルデータ（騎手データ確認）===")
cursor.execute("""
SELECT KAISAI_NEN, KAISAI_GAPPI, KEIBAJO_CODE, RACE_BANGO,
       BAMEI, KISHUMEI_RYAKUSHO, KAKUTEI_CHAKUJUN,
       FUTAN_JURYO, BATAIJU
FROM umagoto_race_joho
WHERE KAISAI_NEN >= '2020'
AND KISHUMEI_RYAKUSHO IS NOT NULL
AND KISHUMEI_RYAKUSHO != ''
ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
LIMIT 20
""")

rows = cursor.fetchall()
for row in rows:
    year, date, venue, race_no, horse, jockey, position, weight, horse_weight = row
    print(f"{year}年{date} {horse}(馬) - {jockey}(騎手) - {position}着")

# 騎手一覧を取得
print("\n=== 騎手一覧（2020年以降）===")
cursor.execute("""
SELECT DISTINCT KISHUMEI_RYAKUSHO, COUNT(*) as ride_count
FROM umagoto_race_joho
WHERE KAISAI_NEN >= '2020'
AND KISHUMEI_RYAKUSHO IS NOT NULL
AND KISHUMEI_RYAKUSHO != ''
GROUP BY KISHUMEI_RYAKUSHO
ORDER BY ride_count DESC
LIMIT 20
""")

jockeys = cursor.fetchall()
for jockey, count in jockeys:
    print(f"{jockey}: {count}騎乗")

connection.close()