@echo off
echo Phase C 動作確認テスト実行中...
echo.

cd /d "%~dp0"
venv\Scripts\python.exe phase_c_simple_test.py

echo.
echo Phase C テスト完了！
pause