#!/bin/bash
# -*- coding: utf-8 -*-
"""
ナレッジファイル差分更新パイプライン
D-Logic → 拡張ナレッジ → 騎手ナレッジ → ViewLogic の順で自動実行
"""

# ログファイル設定
PIPELINE_LOG="knowledge_pipeline.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ログ出力関数
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$PIPELINE_LOG"
}

log_message "=== ナレッジファイル差分更新パイプライン開始 ==="

# 現在の作業ディレクトリを確認
if [ ! -f "update_dlogic_raw_knowledge_incremental_fixed.py" ]; then
    log_message "エラー: 必要なスクリプトファイルが見つかりません"
    exit 1
fi

# 1. D-Logic差分更新の実行状況を確認
log_message "Phase 1: D-Logic差分更新の状況確認中..."

# D-Logicプロセスが実行中かチェック
while pgrep -f "update_dlogic_raw_knowledge_incremental_fixed.py" > /dev/null; do
    log_message "D-Logic差分更新実行中... 30秒待機"
    sleep 30
done

# D-Logicログの最終状況を確認
if tail -5 dlogic_incremental_update.log | grep -q "処理完了\|差分更新完了"; then
    log_message "Phase 1完了: D-Logic差分更新が正常終了"
else
    log_message "Phase 1警告: D-Logic差分更新の状況が不明"
    log_message "最新ログ:"
    tail -3 dlogic_incremental_update.log | tee -a "$PIPELINE_LOG"
fi

# 30秒待機（MySQL負荷軽減）
log_message "MySQL負荷軽減のため30秒待機..."
sleep 30

# 2. 拡張ナレッジファイル差分更新の実行
log_message "Phase 2: 拡張ナレッジファイル差分更新開始"

if [ -f "update_extended_knowledge_incremental_fixed.py" ]; then
    nohup python3 update_extended_knowledge_incremental_fixed.py > extended_knowledge_incremental.log 2>&1 &
    EXTENDED_PID=$!
    log_message "拡張ナレッジファイル差分更新開始 (PID: $EXTENDED_PID)"
    
    # プロセス開始確認
    sleep 10
    if kill -0 $EXTENDED_PID 2>/dev/null; then
        log_message "拡張ナレッジファイル差分更新が正常に開始されました"
    else
        log_message "エラー: 拡張ナレッジファイル差分更新の開始に失敗"
        exit 1
    fi
    
    # 拡張ナレッジ処理の完了を待機
    while kill -0 $EXTENDED_PID 2>/dev/null; do
        log_message "拡張ナレッジファイル差分更新実行中... 60秒待機"
        sleep 60
    done
    
    # 拡張ナレッジログの最終状況を確認
    if tail -5 extended_knowledge_incremental.log | grep -q "処理完了\|差分更新完了"; then
        log_message "Phase 2完了: 拡張ナレッジファイル差分更新が正常終了"
    else
        log_message "Phase 2警告: 拡張ナレッジファイル差分更新の状況が不明"
        log_message "最新ログ:"
        tail -3 extended_knowledge_incremental.log | tee -a "$PIPELINE_LOG"
    fi
else
    log_message "エラー: update_extended_knowledge_incremental_fixed.py が見つかりません"
    exit 1
fi

# 30秒待機（MySQL負荷軽減）
log_message "MySQL負荷軽減のため30秒待機..."
sleep 30

# 3. 騎手ナレッジファイル差分更新の実行
log_message "Phase 3: 騎手ナレッジファイル差分更新開始"

if [ -f "update_jockey_knowledge_incremental.py" ]; then
    nohup python3 update_jockey_knowledge_incremental.py > jockey_knowledge_incremental.log 2>&1 &
    JOCKEY_PID=$!
    log_message "騎手ナレッジファイル差分更新開始 (PID: $JOCKEY_PID)"
    
    # プロセス開始確認
    sleep 10
    if kill -0 $JOCKEY_PID 2>/dev/null; then
        log_message "騎手ナレッジファイル差分更新が正常に開始されました"
    else
        log_message "エラー: 騎手ナレッジファイル差分更新の開始に失敗"
        exit 1
    fi
    
    # 騎手ナレッジ処理の完了を待機
    while kill -0 $JOCKEY_PID 2>/dev/null; do
        log_message "騎手ナレッジファイル差分更新実行中... 60秒待機"
        sleep 60
    done
    
    # 騎手ナレッジログの最終状況を確認
    if tail -5 jockey_knowledge_incremental.log | grep -q "処理完了\|差分更新完了"; then
        log_message "Phase 3完了: 騎手ナレッジファイル差分更新が正常終了"
    else
        log_message "Phase 3警告: 騎手ナレッジファイル差分更新の状況が不明"
        log_message "最新ログ:"
        tail -3 jockey_knowledge_incremental.log | tee -a "$PIPELINE_LOG"
    fi
else
    log_message "Phase 3スキップ: update_jockey_knowledge_incremental.py が見つかりません"
fi

# 30秒待機（MySQL負荷軽減）
log_message "MySQL負荷軽減のため30秒待機..."
sleep 30

# 4. ViewLogicナレッジファイル差分更新の実行
log_message "Phase 4: ViewLogicナレッジファイル差分更新開始"

if [ -f "update_viewlogic_knowledge_incremental.py" ]; then
    nohup python3 update_viewlogic_knowledge_incremental.py > viewlogic_knowledge_incremental.log 2>&1 &
    VIEWLOGIC_PID=$!
    log_message "ViewLogicナレッジファイル差分更新開始 (PID: $VIEWLOGIC_PID)"
    
    # プロセス開始確認
    sleep 10
    if kill -0 $VIEWLOGIC_PID 2>/dev/null; then
        log_message "ViewLogicナレッジファイル差分更新が正常に開始されました"
    else
        log_message "エラー: ViewLogicナレッジファイル差分更新の開始に失敗"
        exit 1
    fi
    
    # ViewLogic処理の完了を待機
    while kill -0 $VIEWLOGIC_PID 2>/dev/null; do
        log_message "ViewLogicナレッジファイル差分更新実行中... 60秒待機"
        sleep 60
    done
    
    # ViewLogicログの最終状況を確認
    if tail -5 viewlogic_knowledge_incremental.log | grep -q "処理完了\|差分更新完了"; then
        log_message "Phase 4完了: ViewLogicナレッジファイル差分更新が正常終了"
    else
        log_message "Phase 4警告: ViewLogicナレッジファイル差分更新の状況が不明"
        log_message "最新ログ:"
        tail -3 viewlogic_knowledge_incremental.log | tee -a "$PIPELINE_LOG"
    fi
else
    log_message "Phase 4スキップ: update_viewlogic_knowledge_incremental.py が見つかりません"
fi

# パイプライン完了レポート
PIPELINE_END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log_message "=== ナレッジファイル差分更新パイプライン完了 ($PIPELINE_END_TIME) ==="

# 全ファイルのサイズを確認
log_message "更新後のナレッジファイルサイズ:"
if [ -f "data/dlogic_raw_knowledge.json" ]; then
    SIZE=$(du -h data/dlogic_raw_knowledge.json | cut -f1)
    log_message "  D-Logic標準: $SIZE"
fi

if [ -f "data/dlogic_extended_knowledge.json" ]; then
    SIZE=$(du -h data/dlogic_extended_knowledge.json | cut -f1)
    log_message "  拡張ナレッジ: $SIZE"
fi

if [ -f "data/jockey_knowledge.json" ]; then
    SIZE=$(du -h data/jockey_knowledge.json | cut -f1)
    log_message "  騎手ナレッジ: $SIZE"
fi

if [ -f "data/viewlogic_knowledge.json" ]; then
    SIZE=$(du -h data/viewlogic_knowledge.json | cut -f1)
    log_message "  ViewLogic: $SIZE"
fi

log_message "パイプライン処理が完了しました。詳細は各ログファイルを確認してください。"

echo "ナレッジファイル差分更新パイプライン完了"