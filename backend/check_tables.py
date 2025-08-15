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
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

print("=== 全テーブル一覧 ===")
for table in tables:
    print(table[0])

# 馬、レース関連のテーブルを探す
print("\n=== UMA/RACE関連テーブル ===")
for table in tables:
    table_name = table[0].lower()
    if 'uma' in table_name or 'race' in table_name or 'kishu' in table_name:
        print(table[0])

connection.close()