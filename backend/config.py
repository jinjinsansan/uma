import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# OpenAI設定
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# 開発用設定
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development') 