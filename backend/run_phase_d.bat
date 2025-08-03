@echo off
echo Phase D: mykeibadb最大活用ナレッジベース構築
echo.

cd /d "%~dp0"

echo 🧪 Phase D クイックテスト実行中...
echo.
venv\Scripts\python.exe scripts\maximum_expansion.py test

echo.
echo ✅ クイックテスト完了
echo.
echo 🚀 フル実行を開始しますか？
echo   Enter: 開始 / Ctrl+C: 中断
pause > nul

echo.
echo 🔄 Phase D フル実行開始...
echo.
venv\Scripts\python.exe scripts\maximum_expansion.py

echo.
echo Phase D 実行完了！
pause