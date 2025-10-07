#!/usr/bin/env python3
"""
キャッシュサービス
OpenAI APIとD-Logic分析結果をキャッシュして負荷軽減
Redis統合版 - Redisが利用可能な場合は優先的に使用
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
from functools import lru_cache
import logging
import itertools
import copy
import os
from pathlib import Path
LOCK_FILE_PATH = Path("/tmp/uma_prewarm.lock")
LOCK_REDIS_KEY = "cache_prewarm_lock:nar_v2"
LOCK_TTL_SECONDS = 1800


def _acquire_prewarm_lock() -> Tuple[bool, bool]:
    """プリウォームの重複実行を防ぐためのロックを取得"""
    redis_lock_acquired = False
    try:
        if cache_service.redis_cache and cache_service.redis_cache.is_connected():
            client = cache_service.redis_cache.client
            if client.set(LOCK_REDIS_KEY, os.getpid(), nx=True, ex=LOCK_TTL_SECONDS):
                redis_lock_acquired = True
                return True, True
    except Exception as exc:  # pragma: no cover - safety
        logger.debug("Prewarm redis lock failed: %s", exc)

    try:
        LOCK_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(LOCK_FILE_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as handle:
            handle.write(str(os.getpid()))
        return True, redis_lock_acquired
    except FileExistsError:
        return False, redis_lock_acquired
    except Exception as exc:  # pragma: no cover - safety
        logger.debug("Prewarm file lock failed: %s", exc)
        return False, redis_lock_acquired


def _release_prewarm_lock(redis_lock_acquired: bool) -> None:
    """取得したプリウォームロックを解放"""
    if redis_lock_acquired:
        try:
            if cache_service.redis_cache and cache_service.redis_cache.is_connected():
                cache_service.redis_cache.client.delete(LOCK_REDIS_KEY)
        except Exception as exc:  # pragma: no cover - safety
            logger.debug("Prewarm redis unlock failed: %s", exc)

    try:
        if LOCK_FILE_PATH.exists():
            LOCK_FILE_PATH.unlink()
    except Exception as exc:  # pragma: no cover - safety
        logger.debug("Prewarm file unlock failed: %s", exc)

logger = logging.getLogger(__name__)

# Redisキャッシュをインポート（利用可能な場合）
try:
    from services.redis_cache import get_redis_cache, RedisCache
    REDIS_AVAILABLE = True
    logger.info("Redis cache module loaded successfully")
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis cache not available, using memory cache only")

class CacheService:
    """メモリベースのキャッシュサービス"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hit_count = 0
        self.miss_count = 0
        
        # Redisクライアントを初期化（利用可能な場合）
        self.redis_cache: Optional[RedisCache] = None
        if REDIS_AVAILABLE:
            try:
                self.redis_cache = get_redis_cache()
                if self.redis_cache.is_connected():
                    logger.info("Redis cache connected successfully")
                else:
                    logger.warning("Redis cache not connected, using memory cache")
                    self.redis_cache = None
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self.redis_cache = None
        
        # TTL設定（用途別）
        self.ttl_settings = {
            'chat_response': timedelta(hours=48),      # チャット応答: 48時間（増加）
            'dlogic_analysis': timedelta(hours=72),    # D-Logic分析: 72時間（増加）
            'imlogic_analysis': timedelta(hours=72),   # IMLogic分析: 72時間
            'ilogic_analysis': timedelta(hours=48),    # I-Logic分析: 48時間
            'flogic_analysis': timedelta(hours=48),    # F-Logic分析: 48時間
            'metalogic_analysis': timedelta(hours=48), # MetaLogic分析: 48時間
            'weather_analysis': timedelta(hours=24),   # 天候適性: 24時間（増加）
            'faq_response': timedelta(days=14),        # FAQ: 14日間（増加）
            'race_analysis': timedelta(hours=12),      # レース分析: 12時間（増加）
            'horse_data': timedelta(days=7),           # 馬データ: 7日間
            'jockey_data': timedelta(days=7),          # 騎手データ: 7日間
            'viewlogic_flow': timedelta(hours=6),      # ViewLogic展開予想
            'viewlogic_trend': timedelta(hours=6),     # ViewLogic傾向分析
            'viewlogic_recommendation': timedelta(hours=6),  # ViewLogic推奨
            'viewlogic_history': timedelta(hours=12),  # ViewLogic過去データ
            'viewlogic_sire': timedelta(hours=24),     # ViewLogic血統分析
        }
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """キャッシュキーを生成（正規化付き）"""
        # データの正規化
        if isinstance(data, dict):
            # 辞書の値を正規化
            normalized_data = {}
            for k, v in data.items():
                # 正規化を削除し、そのまま使用
                normalized_data[k] = v
            data_str = json.dumps(normalized_data, sort_keys=True, ensure_ascii=False)
        elif isinstance(data, list):
            # リストの場合はそのままソート
            data_str = json.dumps(sorted(data) if all(isinstance(x, str) for x in data) else data, ensure_ascii=False)
        else:
            # 文字列の場合はそのまま使用
            data_str = str(data)
        
        # MD5ハッシュでキーを生成
        hash_obj = hashlib.md5(data_str.encode('utf-8'))
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, prefix: str, data: Any) -> Optional[Any]:
        """キャッシュから取得（Redis優先）"""
        key = self._generate_key(prefix, data)
        
        # Redisから取得を試みる
        if self.redis_cache and self.redis_cache.is_connected():
            try:
                redis_key = f"dlogic:{key}"
                value = self.redis_cache.get(redis_key)
                if value is not None:
                    self.hit_count += 1
                    logger.debug(f"Redis cache hit for {redis_key}")
                    return value
            except Exception as e:
                logger.warning(f"Redis get failed: {e}, falling back to memory cache")
        
        # メモリキャッシュから取得
        if key in self.cache:
            entry = self.cache[key]
            # 有効期限チェック
            if datetime.now() < entry['expires_at']:
                self.hit_count += 1
                print(f"📋 キャッシュヒット: {prefix} (ヒット率: {self.get_hit_rate():.1f}%)")
                return entry['value']
            else:
                # 期限切れは削除
                del self.cache[key]
        
        self.miss_count += 1
        return None
    
    def set(self, prefix: str, data: Any, value: Any, ttl_override: Optional[timedelta] = None) -> None:
        """キャッシュに保存（Redis優先）"""
        key = self._generate_key(prefix, data)
        
        # TTL決定
        ttl = ttl_override or self.ttl_settings.get(prefix, timedelta(hours=24))
        
        # Redisに保存を試みる
        if self.redis_cache and self.redis_cache.is_connected():
            try:
                redis_key = f"dlogic:{key}"
                ttl_seconds = int(ttl.total_seconds())
                success = self.redis_cache.set(redis_key, value, ttl=ttl_seconds)
                if success:
                    logger.debug(f"Saved to Redis cache: {redis_key}")
            except Exception as e:
                logger.warning(f"Redis set failed: {e}, saving to memory cache")
        
        # メモリキャッシュにも保存（フォールバック）
        self.cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + ttl,
            'prefix': prefix
        }
        
        # メモリ管理（最大1000エントリ）
        if len(self.cache) > 1000:
            self._cleanup_old_entries()
    
    def _cleanup_old_entries(self):
        """古いエントリを削除"""
        now = datetime.now()
        # 期限切れを削除
        expired_keys = [k for k, v in self.cache.items() if v['expires_at'] < now]
        for key in expired_keys:
            del self.cache[key]
        
        # それでも多い場合は古い順に削除
        if len(self.cache) > 800:
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['created_at']
            )
            for key, _ in sorted_items[:200]:
                del self.cache[key]
    
    def clear_prefix(self, prefix: str):
        """特定のプレフィックスのキャッシュをクリア"""
        keys_to_delete = [k for k, v in self.cache.items() if v.get('prefix') == prefix]
        for key in keys_to_delete:
            del self.cache[key]
        print(f"🗑️ {prefix}のキャッシュをクリア: {len(keys_to_delete)}件")
    
    def get_hit_rate(self) -> float:
        """キャッシュヒット率を取得"""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return (self.hit_count / total) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得"""
        stats = {
            'total_entries': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': self.get_hit_rate(),
            'memory_usage_mb': self._estimate_memory_usage(),
            'entries_by_prefix': {}
        }
        
        # プレフィックス別の統計
        for key, entry in self.cache.items():
            prefix = entry.get('prefix', 'unknown')
            if prefix not in stats['entries_by_prefix']:
                stats['entries_by_prefix'][prefix] = 0
            stats['entries_by_prefix'][prefix] += 1
        
        return stats
    
    def _estimate_memory_usage(self) -> float:
        """メモリ使用量を推定（MB）"""
        # 簡易的な推定
        total_size = 0
        for key, entry in self.cache.items():
            # キーのサイズ
            total_size += len(key.encode('utf-8'))
            # 値のサイズ（JSON化して推定）
            try:
                value_str = json.dumps(entry, ensure_ascii=False)
                total_size += len(value_str.encode('utf-8'))
            except:
                total_size += 1000  # エラー時は1KBと仮定
        
        return total_size / (1024 * 1024)  # MB変換


def _build_nar_sample_races() -> List[Dict[str, Any]]:
    """プリウォームに使用する地方競馬のサンプルレースを生成"""
    try:
        from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
    except Exception as exc:  # pragma: no cover - defensive import
        logger.warning("NAR prewarm: failed to import horse manager: %s", exc)
        return []

    try:
        from services.local_jockey_data_manager import local_jockey_manager
    except Exception as exc:  # pragma: no cover - defensive import
        logger.warning("NAR prewarm: failed to import jockey manager: %s", exc)
        return []

    fallback_horses = [
        "アランバローズ", "ミスティネイル", "キャッスルトップ", "セイカメテオポリス",
        "エメリミット", "マンガン", "ヒカリオーソ", "ブラヴール",
        "ヴァケーション", "トランセンデンス", "ミューチャリー", "デュードヴァン",
        "サヨノグローリー", "ライトウォーリア", "サルサディオーネ", "ノンコノユメ",
        "ティーズダンク", "クリスタルシルバー", "リコーシーウルフ", "カジノフォンテン",
        "ルーチェドーロ", "アングライフェン", "ジョエル", "イグナシオドーロ"
    ]
    fallback_jockeys = [
        "森泰斗", "御神本訓史", "矢野貴之", "笹川翼", "張田昂", "和田譲治",
        "今野忠成", "川島正太郎", "石崎駿", "真島大輔", "町田直希", "山崎誠士",
        "岡村健司", "酒井忍", "内田利雄", "左海誠二", "小杉亮", "藤田凌",
        "吉原寛人", "本橋孝太", "藤本現暉", "本田正重", "小林凌", "江里口裕輝"
    ]

    horses: List[str] = []
    jockeys: List[str] = []

    try:
        if hasattr(local_dlogic_manager_v2, 'get_sample_horses'):
            horses = local_dlogic_manager_v2.get_sample_horses(limit=24) or []
        elif hasattr(local_dlogic_manager_v2, 'get_all_horse_names'):
            horses = (local_dlogic_manager_v2.get_all_horse_names() or [])[:24]
    except Exception as exc:
        logger.warning("NAR prewarm: failed to fetch sample horses: %s", exc)

    try:
        if hasattr(local_jockey_manager, 'get_sample_jockeys'):
            jockeys = local_jockey_manager.get_sample_jockeys(limit=24) or []
        elif hasattr(local_jockey_manager, 'get_all_jockey_names'):
            jockeys = (local_jockey_manager.get_all_jockey_names() or [])[:24]
    except Exception as exc:
        logger.warning("NAR prewarm: failed to fetch sample jockeys: %s", exc)

    if len(horses) < 12:
        original = len(horses)
        existing = set(horses)
        for name in fallback_horses:
            if name not in existing:
                horses.append(name)
                existing.add(name)
            if len(horses) >= 12:
                break
        if len(horses) < 12:
            horses = fallback_horses[:12]
        logger.info("NAR prewarm: using fallback horses (%d->%d)", original, len(horses))

    if len(jockeys) < 12:
        original = len(jockeys)
        existing = set(jockeys)
        for name in fallback_jockeys:
            if name not in existing:
                jockeys.append(name)
                existing.add(name)
            if len(jockeys) >= 12:
                break
        if len(jockeys) < 12:
            jockeys = fallback_jockeys[:12]
        logger.info("NAR prewarm: using fallback jockeys (%d->%d)", original, len(jockeys))

    if not horses or not jockeys:
        logger.warning(
            "NAR prewarm: insufficient sample data (horses=%d, jockeys=%d)",
            len(horses),
            len(jockeys)
        )
        return []

    sample_configs = [
        ("大井", "2025-01-01", "11", "ダート", 1800, "プリウォーム記念"),
        ("川崎", "2025-01-02", "10", "ダート", 1600, "プリウォームカップ"),
        ("船橋", "2025-01-03", "9", "ダート", 1200, "プリウォームスプリント")
    ]

    horse_cycle = itertools.cycle(horses)
    jockey_cycle = itertools.cycle(jockeys)
    headcount = min(12, len(horses), len(jockeys))
    if headcount == 0:
        return []

    sample_races: List[Dict[str, Any]] = []
    for venue, race_date, race_number, track_type, distance, race_name in sample_configs:
        selected_horses = [next(horse_cycle) for _ in range(headcount)]
        selected_jockeys = [next(jockey_cycle) for _ in range(headcount)]
        posts = list(range(1, headcount + 1))
        odds = [round(1.8 + 0.35 * idx, 1) for idx in range(headcount)]
        sample_races.append({
            'race_date': race_date,
            'venue': venue,
            'race_number': race_number,
            'race_name': race_name,
            'distance': distance,
            'track_type': track_type,
            'track_condition': '良',
            'horses': selected_horses,
            'jockeys': selected_jockeys,
            'posts': posts,
            'horse_numbers': posts,
            'sex_ages': [],
            'weights': [],
            'trainers': [],
            'odds': odds,
            'popularities': list(range(1, headcount + 1)),
            'course_type': track_type
        })

    return sample_races


def _prewarm_nar_v2_engines() -> int:
    """地方競馬版V2エンジン群をプリウォーム"""
    sample_races = _build_nar_sample_races()
    if not sample_races:
        return 0

    try:
        from services.v2.ai_handler import V2AIHandler
        from services.local_race_analysis_engine_v2 import local_race_analysis_engine_v2
        from services.local_imlogic_engine_v2 import local_imlogic_engine_v2
        from services.local_flogic_engine_v2 import local_flogic_engine_v2
        from services.local_metalogic_engine_v2 import local_metalogic_engine_v2
        from services.local_viewlogic_engine_v2 import local_viewlogic_engine_v2
        from services.v2.ai_handler_format_advanced import format_flow_prediction_advanced
    except Exception as exc:  # pragma: no cover - defensive import
        logger.error("NAR prewarm: failed to import V2 components: %s", exc)
        return 0

    handler = V2AIHandler()
    default_item_weights = handler._get_default_weights()
    warmed_entries = 0

    for base_race in sample_races:
        race_template = copy.deepcopy(base_race)

        # I-Logicプリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            ilogic_result = local_race_analysis_engine_v2.analyze_race(race_data)
            if isinstance(ilogic_result, dict) and ilogic_result.get('status') == 'success':
                scores = ilogic_result.get('scores') or ilogic_result.get('results') or []
                content = handler._format_ilogic_scores_local(scores, race_data)
                race_info = ilogic_result.get('race_info') or {
                    'venue': race_data.get('venue', ''),
                    'race_number': race_data.get('race_number', ''),
                    'race_name': race_data.get('race_name', '')
                }
                summary = ilogic_result.get('summary') or {}
                item_weights = ilogic_result.get('item_weights') or copy.deepcopy(default_item_weights)
                weights = ilogic_result.get('weights') or {'horse': 70, 'jockey': 30}
                top_horses = ilogic_result.get('top_horses') or [
                    entry.get('horse') for entry in scores if isinstance(entry, dict) and entry.get('horse')
                ][:5]
                analysis_data = {
                    'type': 'ilogic',
                    'analysis_type': ilogic_result.get('analysis_type', 'race_analysis_v2'),
                    'race_info': race_info,
                    'results': scores,
                    'scores': scores,
                    'summary': summary,
                    'item_weights': item_weights,
                    'weights': weights,
                    'top_horses': top_horses
                }
                cache_key = handler._build_cache_key_data('nar_ilogic', race_data)
                handler._save_cached_response('ilogic_analysis', cache_key, content, analysis_data)
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR I-Logic prewarm skipped: %s", exc)

        # IMLogicプリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            imlogic_result = local_imlogic_engine_v2.analyze_race(
                race_data=race_data,
                horse_weight=70,
                jockey_weight=30,
                item_weights=copy.deepcopy(default_item_weights)
            )
            if isinstance(imlogic_result, dict) and imlogic_result.get('status') == 'success':
                cache_extra = {
                    'horse_weight': 70,
                    'jockey_weight': 30,
                    'item_weights': copy.deepcopy(default_item_weights)
                }
                content = handler._format_imlogic_result(imlogic_result, race_data)
                cache_key = handler._build_cache_key_data('nar_imlogic', race_data, extra=cache_extra)
                handler._save_cached_response('imlogic_analysis', cache_key, content, imlogic_result)
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR IMLogic prewarm skipped: %s", exc)

        # F-Logicプリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            odds_values = race_data.get('odds') or []
            horses = race_data.get('horses') or []
            market_odds = {
                horse: float(odds_values[idx])
                for idx, horse in enumerate(horses)
                if idx < len(odds_values) and odds_values[idx]
            }
            flogic_result = local_flogic_engine_v2.analyze_race(
                race_data=race_data,
                market_odds=market_odds
            )
            if isinstance(flogic_result, dict) and flogic_result.get('status') == 'success':
                content = handler._format_flogic_result(flogic_result, race_data)
                analysis_data = {
                    'type': 'flogic',
                    'rankings': flogic_result.get('rankings', []),
                    'has_market_odds': flogic_result.get('has_market_odds', bool(market_odds))
                }
                cache_key = handler._build_cache_key_data('nar_flogic', race_data, extra={'market_odds': market_odds})
                handler._save_cached_response('flogic_analysis', cache_key, content, analysis_data)
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR F-Logic prewarm skipped: %s", exc)

        # MetaLogicプリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            metalogic_result = local_metalogic_engine_v2.analyze_race(race_data)
            if isinstance(metalogic_result, dict) and metalogic_result.get('status') == 'success':
                content = handler._format_metalogic_result(metalogic_result)
                cache_key = handler._build_cache_key_data(
                    'nar_metalogic',
                    race_data,
                    extra={'odds': list(race_data.get('odds') or [])}
                )
                handler._save_cached_response('metalogic_analysis', cache_key, content, metalogic_result)
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR MetaLogic prewarm skipped: %s", exc)

        # ViewLogic展開予想プリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            flow_result = local_viewlogic_engine_v2.predict_race_flow_advanced(race_data)
            if isinstance(flow_result, dict) and flow_result.get('status') == 'success':
                flow_content = format_flow_prediction_advanced(flow_result)
                flow_key = handler._build_cache_key_data(
                    'nar_viewlogic',
                    race_data,
                    extra={'sub_type': 'flow'}
                )
                handler._save_cached_response('viewlogic_flow', flow_key, flow_content, flow_result)
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR ViewLogic flow prewarm skipped: %s", exc)

        # ViewLogic傾向分析プリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            trend_result = local_viewlogic_engine_v2.analyze_course_trend(race_data)
            if isinstance(trend_result, dict) and trend_result.get('status') == 'success':
                trend_content = handler._format_trend_analysis(trend_result)
                trend_key = handler._build_cache_key_data(
                    'nar_viewlogic',
                    race_data,
                    extra={'sub_type': 'trend'}
                )
                handler._save_cached_response('viewlogic_trend', trend_key, trend_content, trend_result)
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR ViewLogic trend prewarm skipped: %s", exc)

        # ViewLogic推奨馬券プリウォーム
        try:
            race_data = copy.deepcopy(race_template)
            recommendation_result = local_viewlogic_engine_v2.recommend_betting_tickets(race_data=race_data)
            if isinstance(recommendation_result, dict) and recommendation_result.get('status') == 'success':
                recommendation_content = handler._format_betting_recommendations(recommendation_result)
                recommendation_key = handler._build_cache_key_data(
                    'nar_viewlogic',
                    race_data,
                    extra={'sub_type': 'recommendation'}
                )
                handler._save_cached_response(
                    'viewlogic_recommendation',
                    recommendation_key,
                    recommendation_content,
                    recommendation_result
                )
                warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR ViewLogic recommendation prewarm skipped: %s", exc)

        # ViewLogic過去データプリウォーム（先頭馬）
        try:
            race_data = copy.deepcopy(race_template)
            horses = race_data.get('horses') or []
            if horses:
                target_horse = horses[0]
                history_result = local_viewlogic_engine_v2.get_horse_history(target_horse)
                if isinstance(history_result, dict) and history_result.get('status') == 'success':
                    progress_message = (
                        "ViewLogic過去データを取得中...\n"
                        f"{target_horse}の履歴を検索しています..."
                    )
                    history_content = handler._format_horse_history(history_result, target_horse)
                    full_content = f"{progress_message}\n\n{history_content}"
                    history_key = handler._build_cache_key_data(
                        'nar_viewlogic',
                        race_data,
                        extra={'sub_type': 'history', 'target_horse': target_horse}
                    )
                    handler._save_cached_response(
                        'viewlogic_history',
                        history_key,
                        full_content,
                        history_result
                    )
                    warmed_entries += 1
        except Exception as exc:
            logger.debug("NAR ViewLogic history prewarm skipped: %s", exc)

    return warmed_entries


# グローバルインスタンス（全インスタンスで共有）
def prewarm_cache():
    """キャッシュをプリウォーミング（G1レース用）"""
    logger.info("Starting cache prewarming for G1 races...")
    lock_acquired, redis_lock_acquired = _acquire_prewarm_lock()
    if not lock_acquired:
        logger.info("Cache prewarming skipped: another worker already running prewarm.")
        return 0

    warmed = 0
    try:
        # G1レースでよく使われる馬名リスト（例）
        popular_horses = [
            "イクイノックス", "ドウデュース", "リバティアイランド",
            "ソダシ", "ジオグリフ", "スターズオンアース"
        ]

        # 主要競馬場
        major_venues = ["東京", "中山", "京都", "阪神"]

        try:
            from services.fast_dlogic_engine import FastDLogicEngine
            engine = FastDLogicEngine()

            for horse_name in popular_horses:
                for venue in major_venues:
                    cache_data = {
                        'horse_name': horse_name,
                        'venue': venue,
                        'analysis_type': 'dlogic',
                        'region': 'jra'
                    }

                    key = cache_service._generate_key('dlogic_analysis', cache_data)

                    if cache_service.redis_cache and cache_service.redis_cache.is_connected():
                        redis_key = f"dlogic:{key}"
                        if cache_service.redis_cache.exists(redis_key):
                            continue

                    try:
                        result = engine.analyze_single_horse(horse_name)
                        cache_service.set(
                            'dlogic_analysis',
                            cache_data,
                            result,
                            ttl_override=timedelta(days=3)
                        )
                        warmed += 1
                        logger.debug(f"Prewarmed JRA cache for {horse_name} at {venue}")
                    except Exception as e:
                        logger.warning(f"Failed to prewarm JRA horse {horse_name}: {e}")

        except Exception as e:
            logger.error(f"Cache prewarming failed for JRA: {e}")

        # 地方競馬(NAR)向けのプリウォーム
        try:
            from services.local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
            local_engine = LocalFastDLogicEngineV2()
            local_manager = local_engine.raw_manager

            local_horses = []
            if hasattr(local_manager, 'get_sample_horses'):
                local_horses = local_manager.get_sample_horses(limit=8)
            elif hasattr(local_manager, 'get_all_horse_names'):
                local_horses = local_manager.get_all_horse_names()[:8]

            local_horses = (local_horses or [])[:8]
            local_venues = ["大井", "川崎", "船橋"]
            local_distances = [1200, 1600, 2000]

            logger.info(
                "NAR D-Logic prewarm coverage: horses=%d venues=%d distances=%d",
                len(local_horses),
                len(local_venues),
                len(local_distances)
            )

            for horse_name in local_horses:
                try:
                    local_manager.calculate_dlogic_realtime(horse_name)
                except Exception as e:
                    logger.debug(f"Shard warm-up failed for {horse_name}: {e}")
                    continue

                for venue in local_venues:
                    for distance in local_distances:
                        cache_data = {
                            'horse_name': horse_name,
                            'venue': venue,
                            'distance': distance,
                            'analysis_type': 'dlogic',
                            'region': 'nar'
                        }

                        key = cache_service._generate_key('dlogic_analysis', cache_data)
                        if cache_service.redis_cache and cache_service.redis_cache.is_connected():
                            redis_key = f"dlogic:{key}"
                            if cache_service.redis_cache.exists(redis_key):
                                continue

                        try:
                            result = local_manager.calculate_dlogic_realtime(horse_name)
                            cache_service.set(
                                'dlogic_analysis',
                                cache_data,
                                result,
                                ttl_override=timedelta(days=2)
                            )
                            warmed += 1
                            logger.debug(f"Prewarmed NAR cache for {horse_name} at {venue} {distance}m")
                        except Exception as e:
                            logger.warning(f"Failed to prewarm NAR horse {horse_name} at {venue} {distance}m: {e}")

        except Exception as e:
            logger.error(f"Cache prewarming failed for NAR: {e}")

        try:
            warmed += _prewarm_nar_v2_engines()
        except Exception as e:
            logger.error(f"Cache prewarming failed for NAR V2 engines: {e}")

        logger.info(f"Cache prewarming completed. Warmed {warmed} entries.")
    finally:
        _release_prewarm_lock(redis_lock_acquired)

    return warmed


def schedule_cache_prewarm():
    """定期的なキャッシュプリウォーミングをスケジュール"""
    import threading
    import time
    
    def prewarm_worker():
        while True:
            try:
                # 毎朝4時にプリウォーミング実行
                now = datetime.now()
                next_run = now.replace(hour=4, minute=0, second=0, microsecond=0)
                if next_run < now:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Next cache prewarm scheduled in {wait_seconds/3600:.1f} hours")
                time.sleep(wait_seconds)
                
                # プリウォーミング実行
                prewarm_cache()
                
            except Exception as e:
                logger.error(f"Prewarm scheduler error: {e}")
                time.sleep(3600)  # エラー時は1時間後に再試行
    
    # バックグラウンドスレッドで実行
    thread = threading.Thread(target=prewarm_worker, daemon=True)
    thread.start()
    logger.info("Cache prewarm scheduler started")


# グローバルインスタンス（全インスタンスで共有）
cache_service = CacheService()


# デコレータ関数
def cached(prefix: str, ttl: Optional[timedelta] = None):
    """キャッシュデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # キャッシュキー用のデータ
            cache_data = {
                'args': args,
                'kwargs': kwargs
            }
            
            # キャッシュチェック
            cached_value = cache_service.get(prefix, cache_data)
            if cached_value is not None:
                return cached_value
            
            # 実行してキャッシュ
            result = func(*args, **kwargs)
            cache_service.set(prefix, cache_data, result, ttl)
            return result
        
        return wrapper
    return decorator