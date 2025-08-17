import sys
sys.path.append('.')
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print('Supabaseの環境変数が設定されていません')
    exit(1)

supabase = create_client(url, key)

# 実際のユーザー数を確認
result = supabase.table('users').select('id', count='exact').execute()
print(f'実際のユーザー数: {result.count}')

# 最新のユーザーを確認
latest_users = supabase.table('users').select('email, created_at').order('created_at', desc=True).limit(5).execute()
print('\n最新の5ユーザー:')
for user in latest_users.data:
    print(f'  - {user["email"]} ({user["created_at"]})')

# 今日作成されたユーザー数を確認
from datetime import datetime
today_start = datetime.now().strftime('%Y-%m-%d') + 'T00:00:00'
today_users = supabase.table('users').select('id', count='exact').gte('created_at', today_start).execute()
print(f'\n今日作成されたユーザー数: {today_users.count}')

