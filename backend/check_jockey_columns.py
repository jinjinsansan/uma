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

# umagoto_race_johoテーブルの構造を確認
print("=== umagoto_race_joho テーブル構造 ===")
cursor.execute("DESCRIBE umagoto_race_joho")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]}")

# サンプルデータを取得
print("\n=== サンプルデータ（最新10件）===")
cursor.execute("""
SELECT year, monthday, jyocd, kaiji, nichiji, racenum, 
       wakuban, umaban, kettonum, bamei, seibetsu_code,
       barei, keiro_code, futan_juryo, kishumei, bataiju,
       zogensa, kakuteijyuni
FROM umagoto_race_joho
WHERE year >= 2020
AND kishumei IS NOT NULL
ORDER BY year DESC, monthday DESC
LIMIT 10
""")

rows = cursor.fetchall()
for row in rows:
    print(f"{row[0]}年{row[1]} {row[9]}(馬名) - {row[14]}(騎手) - {row[17]}着")

# 騎手マスターも確認
print("\n=== kishu_master テーブル構造 ===")
cursor.execute("DESCRIBE kishu_master")
columns = cursor.fetchall()
for col in columns[:10]:
    print(f"{col[0]}: {col[1]}")

connection.close()