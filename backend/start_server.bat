@echo off
echo Phase C サーバー起動中...
echo.

cd /d "%~dp0"
echo サーバーを http://localhost:8001 で起動します
echo.
echo ブラウザで以下のURLにアクセスしてください:
echo   基本動作: http://localhost:8001/
echo   本日レース: http://localhost:8001/api/today-races
echo   東京3R詳細: http://localhost:8001/api/race-detail/tokyo_3r
echo   API仕様書: http://localhost:8001/docs
echo.
echo サーバーを停止するには Ctrl+C を押してください
echo.

venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8001 --reload