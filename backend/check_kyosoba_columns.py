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

# kyosoba_master2テーブルの構造を確認
print("=== kyosoba_master2 テーブル構造 ===")
cursor.execute("DESCRIBE kyosoba_master2")
columns = cursor.fetchall()
for col in columns:
    if 'ketto' in col[0].lower() or 'father' in col[0].lower() or 'sire' in col[0].lower() or 'ch' in col[0].lower():
        print(f"{col[0]}: {col[1]}")

# サンプルデータを確認
print("\n=== サンプルデータ ===")
cursor.execute("SELECT * FROM kyosoba_master2 LIMIT 3")
rows = cursor.fetchall()

# カラム名を取得
cursor.execute("SHOW COLUMNS FROM kyosoba_master2")
column_names = [col[0] for col in cursor.fetchall()]
print("\n=== 全カラム名 ===")
for col_name in column_names:
    print(col_name)

connection.close()