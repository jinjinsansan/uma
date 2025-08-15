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

# 利用可能なテーブルを確認
print("=== 利用可能なテーブル ===")
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
for table in tables:
    if 'uma' in table[0].lower() or 'race' in table[0].lower():
        print(table[0])

connection.close()