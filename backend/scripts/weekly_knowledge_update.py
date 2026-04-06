#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
週次ナレッジファイル全自動更新スクリプト
毎週月曜12:00にWindows Task Schedulerから実行

処理内容:
1. JRA馬ナレッジ（全件再構築、最新9走）
2. JRA騎手ナレッジ（全件再構築）
3. NAR馬ナレッジ（全件再構築、最新9走、スケジュールマスター補正）
4. NAR騎手ナレッジ（全件再構築、スケジュールマスター補正）
5. 全ファイルをCloudflare R2にアップロード
6. 結果をログ出力（オプション: Telegram通知）
"""

import subprocess
import sys
import os
import json
import time
import logging
from datetime import datetime

# =============================================================================
# 設定
# =============================================================================

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPTS_DIR, '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# R2 CDN設定
R2_ENDPOINT = 'https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com'
R2_ACCESS_KEY = '9e66f7edadb758346ff3a3c65464ef13'
R2_SECRET_KEY = 'bc8863b26285fa64fbf9b58621550f0519ae233c5eb4b21bba9427a422306ec6'
R2_BUCKET = 'dlogic-knowledge-files'
R2_PUBLIC_URL = 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev'

# Telegram通知（オプション）
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# 更新対象スクリプト
TASKS = [
    {
        'name': 'JRA馬ナレッジ',
        'script': 'create_jra_knowledge_v2.py',
        'output_pattern': 'jra_knowledge_quality_{date}.json',
        'r2_key': 'jra_knowledge_quality_{date}.json',
        'r2_latest_key': 'jra_knowledge_latest.json',
    },
    {
        'name': 'JRA騎手ナレッジ',
        'script': 'create_jra_jockey_knowledge.py',
        'output_pattern': 'jra_jockey_knowledge_{date}.json',
        'r2_key': 'jra_jockey_knowledge_{date}.json',
        'r2_latest_key': 'jra_jockey_knowledge_latest.json',
    },
    {
        'name': 'NAR馬ナレッジ',
        'script': 'create_all_nar_knowledge.py',
        'output_pattern': 'all_nar_unified_knowledge_{date}.json',
        'r2_key': 'all_nar_unified_knowledge_{date}.json',
        'r2_latest_key': 'all_nar_unified_knowledge_latest.json',
    },
    {
        'name': 'NAR騎手ナレッジ',
        'script': 'create_all_nar_jockey_knowledge.py',
        'output_pattern': 'all_nar_jockey_knowledge_{date}.json',
        'r2_key': 'all_nar_jockey_knowledge_{date}.json',
        'r2_latest_key': 'all_nar_jockey_knowledge_latest.json',
    },
]


# =============================================================================
# ロガー設定
# =============================================================================

def setup_logging():
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(LOG_DIR, f'weekly_update_{today}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger(__name__)


# =============================================================================
# R2アップロード
# =============================================================================

def upload_to_r2(filepath, r2_key, logger):
    """ファイルをCloudflare R2にアップロード"""
    try:
        import boto3
        from botocore.config import Config

        s3 = boto3.client('s3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"  R2アップロード: {r2_key} ({file_size_mb:.1f}MB)")

        s3.upload_file(
            filepath, R2_BUCKET, r2_key,
            ExtraArgs={'ContentType': 'application/json'}
        )

        url = f"{R2_PUBLIC_URL}/{r2_key}"
        logger.info(f"  完了: {url}")
        return url

    except Exception as e:
        logger.error(f"  R2アップロードエラー: {e}")
        return None


# =============================================================================
# Telegram通知
# =============================================================================

def send_telegram(message, logger):
    """Telegram通知を送信（設定がある場合のみ）"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
        }, timeout=10)
    except Exception as e:
        logger.warning(f"Telegram通知失敗: {e}")


# =============================================================================
# VPSバックエンド再起動
# =============================================================================

VPS_HOST = 'root@220.158.24.157'
VPS_SERVICES_DIR = '/opt/dlogic/backend/services'
LOCAL_SERVICES_DIR = os.path.join(SCRIPTS_DIR, '..', 'services')

# 週次更新後にVPSへ同期すべきファイル（CDN URL更新を含むもの）
SYNC_FILES = [
    'dlogic_raw_data_manager.py',
    'jockey_data_manager.py',
    'local_dlogic_raw_data_manager_v2.py',
    'local_jockey_data_manager.py',
    'local_imlogic_engine.py',
    'local_fast_dlogic_engine.py',
]


def restart_vps_backend(logger):
    """サービスファイルをVPSに同期し、バックエンドを再起動する"""
    try:
        # 1. 変更されたサービスファイルをVPSに転送
        logger.info("\nVPSへサービスファイル同期中...")
        for filename in SYNC_FILES:
            local_path = os.path.join(LOCAL_SERVICES_DIR, filename)
            if not os.path.exists(local_path):
                logger.warning(f"  スキップ（未発見）: {filename}")
                continue

            scp_cmd = f'scp "{local_path}" {VPS_HOST}:{VPS_SERVICES_DIR}/{filename}'
            result = subprocess.run(
                scp_cmd, shell=True, capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                logger.info(f"  同期OK: {filename}")
            else:
                logger.error(f"  同期NG: {filename} — {result.stderr.strip()}")

        # 2. ローカルキャッシュ削除 + バックエンド再起動
        logger.info("VPSバックエンド再起動中...")
        ssh_cmd = (
            f'ssh {VPS_HOST} '
            '"rm -f /opt/dlogic/backend/data/dlogic_raw_knowledge.json '
            '/opt/dlogic/backend/data/jockey_knowledge.json '
            '/tmp/local_dlogic_raw_knowledge_v2.json '
            '/tmp/local_jockey_knowledge.json 2>/dev/null; '
            'systemctl restart dlogic-backend && sleep 3 && systemctl is-active dlogic-backend"'
        )
        result = subprocess.run(
            ssh_cmd, shell=True, capture_output=True, text=True, timeout=60,
        )
        status = result.stdout.strip()
        if status == 'active':
            logger.info(f"  VPSバックエンド再起動完了: {status}")
            return True
        else:
            logger.error(f"  VPSバックエンド状態: {status}")
            logger.error(f"  stderr: {result.stderr.strip()}")
            return False

    except Exception as e:
        logger.error(f"  VPS再起動エラー: {e}")
        return False


# =============================================================================
# JRA レースレベル計算 + VPS Redis 投入
# =============================================================================

# netkeita リポジトリの calc_race_level.py パス
RACE_LEVEL_SCRIPT = os.path.normpath(
    os.path.join(SCRIPTS_DIR, '..', '..', '..', '..', 'netkeita', 'scripts', 'calc_race_level.py')
)
# フォールバック: 環境変数で指定
RACE_LEVEL_SCRIPT_ALT = os.environ.get(
    'RACE_LEVEL_SCRIPT',
    r'E:\dev\Cusor\netkeita\scripts\calc_race_level.py',
)


def run_race_level_update(date_str, logger):
    """JRA レースレベルを自前DB計算し、VPS Redis に投入する。

    1. ローカルで calc_race_level.py を実行 (PostgreSQL → JSON)
    2. JSON を VPS に SCP
    3. VPS で Redis に投入
    """
    logger.info(f"\n{'='*50}")
    logger.info("[JRAレースレベル更新]")
    logger.info(f"{'='*50}")

    # スクリプトパス解決
    script_path = RACE_LEVEL_SCRIPT if os.path.exists(RACE_LEVEL_SCRIPT) else RACE_LEVEL_SCRIPT_ALT
    if not os.path.exists(script_path):
        logger.error(f"  calc_race_level.py 未発見: {script_path}")
        return False

    script_dir = os.path.dirname(script_path)
    json_filename = f'jra_race_level_{date_str}.json'
    json_path = os.path.join(script_dir, json_filename)

    # Step 1: ローカルで計算
    logger.info(f"  実行中: {os.path.basename(script_path)}")
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=script_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300,
        )
        elapsed = time.time() - start_time
        logger.info(f"  実行時間: {elapsed:.0f}秒")

        if result.returncode != 0:
            logger.error(f"  終了コード: {result.returncode}")
            logger.error(f"  stderr: {result.stderr[-500:]}")
            return False
    except Exception as e:
        logger.error(f"  実行エラー: {e}")
        return False

    if not os.path.exists(json_path):
        logger.error(f"  JSON未発見: {json_path}")
        return False

    file_size_mb = os.path.getsize(json_path) / (1024 * 1024)
    logger.info(f"  出力: {json_filename} ({file_size_mb:.1f}MB)")

    # Step 2: VPS に SCP
    vps_tmp = '/tmp/jra_race_level.json'
    scp_cmd = f'scp "{json_path}" {VPS_HOST}:{vps_tmp}'
    try:
        result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"  SCP失敗: {result.stderr.strip()}")
            return False
        logger.info(f"  VPS転送完了")
    except Exception as e:
        logger.error(f"  SCP エラー: {e}")
        return False

    # Step 3: VPS で Redis 投入
    redis_load_script = (
        "import json, redis; "
        "r = redis.Redis(host='127.0.0.1', port=6379, db=3, decode_responses=True); "
        f"data = json.load(open('{vps_tmp}', encoding='utf-8')); "
        "pipe = r.pipeline(transaction=False); "
        "[pipe.set(f'nk:racelevel:{k}', json.dumps(v, ensure_ascii=False), ex=86400*365) for k, v in data.items()]; "
        "pipe.execute(); "
        f"print(f'Loaded {{len(data)}} entries')"
    )
    ssh_cmd = f'ssh {VPS_HOST} "python3 -c \\"{redis_load_script}\\" && rm {vps_tmp}"'
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.error(f"  Redis投入失敗: {result.stderr.strip()}")
            return False
        logger.info(f"  Redis投入完了: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"  Redis投入エラー: {e}")
        return False

    return True


# =============================================================================
# メイン処理
# =============================================================================

def run_task(task, date_str, logger):
    """単一タスクを実行"""
    script_path = os.path.join(SCRIPTS_DIR, task['script'])

    if not os.path.exists(script_path):
        logger.error(f"  スクリプト未発見: {script_path}")
        return None

    logger.info(f"  実行中: {task['script']}")
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=1800,  # 30分タイムアウト
        )

        elapsed = time.time() - start_time
        logger.info(f"  実行時間: {elapsed:.0f}秒")

        if result.returncode != 0:
            logger.error(f"  終了コード: {result.returncode}")
            logger.error(f"  stderr: {result.stderr[-500:]}")
            return None

        # 出力ファイルを探す
        output_file = task['output_pattern'].replace('{date}', date_str)
        output_path = os.path.join(SCRIPTS_DIR, output_file)

        if os.path.exists(output_path):
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"  出力: {output_file} ({file_size_mb:.1f}MB)")
            return output_path
        else:
            logger.error(f"  出力ファイル未発見: {output_file}")
            # stdoutからファイルサイズ等の情報を表示
            for line in result.stdout.split('\n')[-20:]:
                if line.strip():
                    logger.info(f"    {line.strip()}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"  タイムアウト（30分）")
        return None
    except Exception as e:
        logger.error(f"  実行エラー: {e}")
        return None


def main():
    logger = setup_logging()
    date_str = datetime.now().strftime('%Y%m%d')

    logger.info("=" * 70)
    logger.info("週次ナレッジファイル全自動更新")
    logger.info("=" * 70)
    logger.info(f"日付: {date_str}")
    logger.info(f"作業ディレクトリ: {SCRIPTS_DIR}")

    results = {}
    total_start = time.time()

    for task in TASKS:
        logger.info(f"\n{'='*50}")
        logger.info(f"[{task['name']}]")
        logger.info(f"{'='*50}")

        # 1. スクリプト実行
        output_path = run_task(task, date_str, logger)

        if not output_path:
            results[task['name']] = {'status': 'FAILED', 'url': None}
            continue

        # 2. R2アップロード（日付付き）
        r2_key = task['r2_key'].replace('{date}', date_str)
        url = upload_to_r2(output_path, r2_key, logger)

        # 3. R2アップロード（latestキー = 常に最新を参照するエイリアス）
        latest_url = None
        if url and task.get('r2_latest_key'):
            latest_url = upload_to_r2(output_path, task['r2_latest_key'], logger)

        results[task['name']] = {
            'status': 'OK' if url else 'UPLOAD_FAILED',
            'url': url,
            'latest_url': latest_url,
            'file_size_mb': round(os.path.getsize(output_path) / (1024 * 1024), 1),
        }

        # 生成済みファイル削除（R2にアップ済みなので）
        # ※ 容量節約のため。残したい場合はコメントアウト
        # os.remove(output_path)

    # =============================================================================
    # サマリー
    # =============================================================================
    total_elapsed = time.time() - total_start

    logger.info(f"\n{'='*70}")
    logger.info("更新結果サマリー")
    logger.info(f"{'='*70}")
    logger.info(f"総実行時間: {total_elapsed:.0f}秒 ({total_elapsed/60:.1f}分)")

    all_ok = True
    summary_lines = [f"週次ナレッジ更新 {date_str}\n"]

    for name, result in results.items():
        status_icon = "OK" if result['status'] == 'OK' else "NG"
        logger.info(f"  [{status_icon}] {name}: {result['status']}")
        if result.get('url'):
            logger.info(f"       URL: {result['url']}")
            logger.info(f"       Latest: {result.get('latest_url', 'N/A')}")
            logger.info(f"       Size: {result.get('file_size_mb', '?')}MB")
        summary_lines.append(f"[{status_icon}] {name} ({result.get('file_size_mb', '?')}MB)")

        if result['status'] != 'OK':
            all_ok = False

    logger.info(f"\n最終結果: {'全件成功' if all_ok else '一部失敗あり'}")
    logger.info(f"ログ: {os.path.join(LOG_DIR, f'weekly_update_{date_str}.log')}")

    # =============================================================================
    # JRA レースレベル計算 + VPS Redis 投入
    # =============================================================================
    race_level_ok = run_race_level_update(date_str, logger)
    if race_level_ok:
        summary_lines.append("JRAレースレベル更新: OK")
    else:
        summary_lines.append("JRAレースレベル更新: NG")

    # =============================================================================
    # VPSバックエンド再起動 + サービスファイル同期
    # =============================================================================
    if all_ok:
        restart_ok = restart_vps_backend(logger)
        if restart_ok:
            summary_lines.append("VPSバックエンド再起動: OK")
        else:
            summary_lines.append("VPSバックエンド再起動: NG (手動で要確認)")

    # Telegram通知
    summary_lines.append(f"\n総実行時間: {total_elapsed/60:.1f}分")
    summary_lines.append("全件成功" if all_ok else "一部失敗あり")
    send_telegram('\n'.join(summary_lines), logger)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
