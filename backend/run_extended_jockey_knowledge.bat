@echo off
echo ========================================
echo 拡張版騎手ナレッジファイル作成
echo 過去9回分データ + 全期間統計
echo ========================================
echo.

REM Pythonスクリプト実行
python create_extended_jockey_knowledge.py

echo.
echo 処理が完了しました。
echo ログファイル: extended_jockey_knowledge.log
echo 出力ファイル: data/extended_jockey_knowledge.json
echo.
pause