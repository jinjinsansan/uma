#!/usr/bin/env python3
"""
地方競馬版D-Logic生データナレッジマネージャー V2
完全に独立した実装（親クラスを継承しない）
"""
import json
import os
import logging
import threading
import time
from collections import OrderedDict
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalDLogicRawDataManagerV2:
    """地方競馬版D-Logic生データ管理システム（独立版）"""
    
    def __init__(self):
        """初期化：地方競馬版専用"""
        # キャッシュファイルパス（Renderでは/tmpを使用）
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        if os.environ.get('RENDER'):
            # Renderでは書き込み可能な/tmpディレクトリを使用
            base_dir = '/tmp'

        self.knowledge_file = os.path.join(base_dir, 'local_dlogic_raw_knowledge_v2.json')
        self.cache_dir = os.path.join(base_dir, 'local_dlogic_cache')
        self.index_file = os.path.join(self.cache_dir, 'index.json')
        self._horse_index: Dict[str, Dict[str, str]] = {}
        self._meta_info: Dict[str, Any] = {}
        self._shard_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._shard_lock = threading.Lock()
        self._max_shard_cache = int(os.environ.get("LOCAL_DLOGIC_SHARD_CACHE", "6"))
        self._shard_size = int(os.environ.get("LOCAL_DLOGIC_SHARD_SIZE", "750"))
        self._download_timeout = int(os.environ.get("LOCAL_DLOGIC_DOWNLOAD_TIMEOUT", "300"))
        
        # CDN URL
        self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"
        
        logger.info("🏇 地方競馬版D-LogicマネージャーV2初期化: cache=%s", self.knowledge_file)

        # ロード制御
        self._knowledge_data: Optional[Dict[str, Any]] = None
        self._load_lock = threading.Lock()
        self._last_loaded_at: Optional[datetime] = None

        # 計算キャッシュ制御（JRA版と同等の仕組み）
        self._calculation_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._cache_log_interval: int = 20
        self._max_cache_size: int = int(os.environ.get("LOCAL_DLOGIC_CACHE_SIZE", "500"))
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """ナレッジファイルの読み込み"""
        # キャッシュファイルが存在する場合
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'horses' in data:
                    horse_count = len(data['horses'])
                    logger.info("📂 地方競馬ナレッジ: キャッシュから読み込み (%s頭)", horse_count)
                    self._save_sharded_cache(data)
                    return data

                logger.warning("⚠️ 地方競馬ナレッジ: キャッシュ構造が不正のため再取得します")
            except Exception as e:
                logger.warning("⚠️ 地方競馬ナレッジ: キャッシュ読み込みエラー (%s)", e)
        
        # CDNからダウンロード
        return self._download_from_cdn()
    
    def _download_from_cdn(self) -> Dict[str, Any]:
        """CDNからダウンロード（ストリーミング対応）"""
        try:
            logger.info("📥 地方競馬ナレッジ: CDNからダウンロード開始 (%s)", self.cdn_url)
            
            # ストリーミングダウンロード（メモリ効率化）
            response = requests.get(self.cdn_url, stream=True, timeout=(10, self._download_timeout))
            
            if response.status_code == 200:
                # コンテンツサイズを確認
                content_length = response.headers.get('content-length')
                if content_length:
                    logger.info("📦 地方競馬ナレッジ: ファイルサイズ %.1fMB", int(content_length) / 1024 / 1024)
                
                # ストリーミングで内容を取得
                content = b''
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                start_time = time.monotonic()
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        content += chunk
                        downloaded += len(chunk)
                        if content_length and downloaded % (10 * chunk_size) == 0:
                            progress = (downloaded / int(content_length)) * 100
                            logger.debug("📥 地方競馬ナレッジ: ダウンロード進捗 %.1f%%", progress)
                        if time.monotonic() - start_time > self._download_timeout:
                            raise requests.exceptions.Timeout("Streaming download exceeded timeout")
                
                logger.info("🔄 地方競馬ナレッジ: JSONパース中")
                data = json.loads(content.decode('utf-8'))
                
                # データ構造を確認（馬名が直接キーになっている）
                if isinstance(data, dict) and 'horses' not in data:
                    horse_count = len(data)
                    logger.info("✅ 地方競馬ナレッジ: ダウンロード完了 (%s頭)", horse_count)
                    
                    # horsesキーでラップ
                    wrapped_data = {
                        "meta": {
                            "version": "2.0",
                            "type": "local_racing",
                            "created_at": datetime.now().isoformat()
                        },
                        "horses": data
                    }
                    
                    # キャッシュに保存
                    self._write_full_cache(wrapped_data)
                    self._save_sharded_cache(wrapped_data)
                    return wrapped_data
                else:
                    # 既にラップされている
                    horse_count = len(data.get('horses', {}))
                    logger.info("✅ 地方競馬ナレッジ: ダウンロード完了 (%s頭)", horse_count)
                    self._write_full_cache(data)
                    self._save_sharded_cache(data)
                    return data
            else:
                logger.error("❌ 地方競馬ナレッジ: ダウンロード失敗 HTTP %s", response.status_code)
        except requests.exceptions.Timeout:
            logger.error("❌ 地方競馬ナレッジ: ダウンロードタイムアウト (300秒)")
        except json.JSONDecodeError as e:
            logger.error("❌ 地方競馬ナレッジ: JSONパースエラー (%s)", e)
        except Exception as e:
            logger.error("❌ 地方競馬ナレッジ: ダウンロードエラー (%s)", e)
        
        # フォールバック
        logger.warning("⚠️ 地方競馬ナレッジ: CDN取得失敗のため空データで初期化")
        return {"horses": {}}
    
    def _write_full_cache(self, data: Dict[str, Any]):
        """元の単一JSONキャッシュを書き出し"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            logger.info("💾 地方競馬ナレッジ: キャッシュ保存完了")
        except Exception as e:
            logger.warning("⚠️ 地方競馬ナレッジ: キャッシュ保存失敗 (%s)", e)

    def _shard_filename(self, shard_id: int) -> str:
        return f"shard_{shard_id:05d}.json"

    def _write_shard(self, shard_id: int, shard_data: Dict[str, Any]):
        os.makedirs(self.cache_dir, exist_ok=True)
        shard_path = os.path.join(self.cache_dir, self._shard_filename(shard_id))
        with open(shard_path, 'w', encoding='utf-8') as f:
            json.dump(shard_data, f, ensure_ascii=False)

    def _save_sharded_cache(self, data: Dict[str, Any]):
        horses = data.get('horses', {})
        if not horses:
            return

        os.makedirs(self.cache_dir, exist_ok=True)

        # 既存シャードをクリーンアップ
        for entry in os.listdir(self.cache_dir):
            if entry.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, entry))
                except OSError:
                    logger.warning("⚠️ 地方競馬ナレッジ: 古いシャード削除に失敗 (%s)", entry)

        index: Dict[str, Dict[str, str]] = {}
        shard_data: Dict[str, Any] = {}
        shard_id = 0
        count = 0

        for horse_name, horse_payload in horses.items():
            if count > 0 and count % self._shard_size == 0:
                self._write_shard(shard_id, shard_data)
                shard_id += 1
                shard_data = {}
            shard_data[horse_name] = horse_payload
            index[horse_name] = {"file": self._shard_filename(shard_id)}
            count += 1

        if shard_data:
            self._write_shard(shard_id, shard_data)

        index_content = {
            "meta": data.get('meta', {}),
            "generated_at": datetime.now().isoformat(),
            "shard_count": shard_id + 1,
            "horses": index
        }

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_content, f, ensure_ascii=False)

        self._horse_index = index
        self._meta_info = index_content.get('meta', {})

    def _load_index(self) -> bool:
        if not os.path.exists(self.index_file):
            return False
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            horses = index_data.get('horses', {})
            if not horses:
                return False
            self._horse_index = horses
            self._meta_info = index_data.get('meta', {})
            logger.info("📂 地方競馬ナレッジ: シャードインデックス読込 (%s頭)", len(self._horse_index))
            return True
        except Exception as e:
            logger.warning("⚠️ 地方競馬ナレッジ: シャードインデックス読込失敗 (%s)", e)
            return False

    def _load_shard(self, shard_file: str) -> Dict[str, Any]:
        with self._shard_lock:
            if shard_file in self._shard_cache:
                # LRU 更新
                self._shard_cache.move_to_end(shard_file)
                return self._shard_cache[shard_file]

            shard_path = os.path.join(self.cache_dir, shard_file)
            try:
                with open(shard_path, 'r', encoding='utf-8') as f:
                    shard_data = json.load(f)
            except FileNotFoundError:
                logger.warning("⚠️ 地方競馬ナレッジ: シャード %s が見つかりません。再構築を試みます", shard_file)
                self._knowledge_data = None
                self._horse_index = {}
                self._meta_info = {}
                self._shard_cache.clear()
                if os.path.exists(self.knowledge_file):
                    data = self._load_knowledge()
                    self._knowledge_data = data
                    self._last_loaded_at = datetime.now()
                    if not self._horse_index:
                        self._load_index()
                    return self._load_shard(shard_file)
                raise

            self._shard_cache[shard_file] = shard_data
            self._shard_cache.move_to_end(shard_file)
            if len(self._shard_cache) > self._max_shard_cache:
                self._shard_cache.popitem(last=False)

            return shard_data

    def _get_horse_entry(self, horse_name: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if self._knowledge_data is not None:
            return self._knowledge_data.get('horses', {}).get(horse_name)

        shard_info = self._horse_index.get(horse_name)
        if not shard_info:
            return None

        shard_file = shard_info.get('file')
        if not shard_file:
            return None

        shard_data = self._load_shard(shard_file)
        return shard_data.get(horse_name)

    def _ensure_loaded(self):
        if self._knowledge_data is not None:
            return

        with self._load_lock:
            if self._knowledge_data is not None:
                return

            if self._load_index():
                self._last_loaded_at = datetime.now()
                logger.info("✅ 地方競馬ナレッジ: インデックスのみロード完了 (%s頭)", len(self._horse_index))
                return

            data = self._load_knowledge()
            self._knowledge_data = data
            self._last_loaded_at = datetime.now()

            horse_count = len(data.get('horses', {}))
            logger.info("✅ 地方競馬ナレッジ: フルデータロード完了 (%s頭)", horse_count)

            if not self._horse_index:
                self._load_index()

    @property
    def knowledge_data(self) -> Dict[str, Any]:
        self._ensure_loaded()

        if self._knowledge_data is None and self._horse_index:
            logger.debug("地方競馬ナレッジ: シャードからインメモリデータを組み立てています (一時的に重い処理)")
            horses: Dict[str, Any] = {}
            loaded_files = set()
            for info in self._horse_index.values():
                shard_file = info.get('file')
                if not shard_file or shard_file in loaded_files:
                    continue
                shard_data = self._load_shard(shard_file)
                horses.update(shard_data)
                loaded_files.add(shard_file)

            self._knowledge_data = {
                "meta": self._meta_info,
                "horses": horses
            }

        return self._knowledge_data or {"horses": {}}
    
    def get_raw_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬の生データを取得"""
        races = self._get_horse_entry(horse_name)
        if races is None:
            return None
        
        # 地方競馬版は配列形式なので、JRA版と同じ形式に変換
        if isinstance(races, list):
            return {
                "horse_name": horse_name,
                "races": races,
                "race_count": len(races)
            }
        # 既にJRA形式の場合はそのまま返す
        return races
    
    def get_horse_raw_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬の生データを取得（互換性のため別名も提供）"""
        return self.get_raw_horse_data(horse_name)
    
    def get_all_horse_names(self) -> list:
        """全馬名リストを取得"""
        if self._horse_index:
            return list(self._horse_index.keys())
        return list(self.knowledge_data.get('horses', {}).keys())
    
    def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬データを取得（ViewLogicとの互換性のため）"""
        return self.get_horse_raw_data(horse_name)
    
    def is_loaded(self) -> bool:
        """データがロードされているか確認"""
        if self._knowledge_data is not None:
            return bool(self._knowledge_data.get('horses'))
        return bool(self._horse_index)
    
    def calculate_dlogic_realtime(self, horse_name: str) -> Dict[str, Any]:
        """生データからリアルタイムD-Logic計算（メモリキャッシュ対応）"""
        # メモリキャッシュチェック
        with self._cache_lock:
            cached = self._calculation_cache.get(horse_name)
            if cached is not None:
                self._cache_hits += 1
                total_requests = self._cache_hits + self._cache_misses
                if total_requests % self._cache_log_interval == 0:
                    hit_rate = (self._cache_hits / total_requests) * 100 if total_requests else 0.0
                    logger.info(
                        "📊 地方D-Logicキャッシュ: hit=%s miss=%s hit_rate=%.1f%%", 
                        self._cache_hits,
                        self._cache_misses,
                        hit_rate
                    )
                return cached

        # キャッシュミス時の処理
        self._cache_misses += 1

        raw_data = self.get_horse_raw_data(horse_name)
        if not raw_data:
            return {
                "horse_name": horse_name,
                "total_score": -1,  # データ不足マーカー
                "error": f"{horse_name}のデータベースにデータがありません",
                "data_available": False
            }
        
        # 12項目をリアルタイム計算
        scores = {
            "1_distance_aptitude": self._calc_distance_aptitude(raw_data),
            "2_bloodline_evaluation": self._calc_bloodline_evaluation(raw_data),
            "3_jockey_compatibility": self._calc_jockey_compatibility(raw_data),
            "4_trainer_evaluation": self._calc_trainer_evaluation(raw_data),
            "5_track_aptitude": self._calc_track_aptitude(raw_data),
            "6_weather_aptitude": self._calc_weather_aptitude(raw_data),
            "7_popularity_factor": self._calc_popularity_factor(raw_data),
            "8_weight_impact": self._calc_weight_impact(raw_data),
            "9_horse_weight_impact": self._calc_horse_weight_impact(raw_data),
            "10_corner_specialist_degree": self._calc_corner_specialist(raw_data),
            "11_margin_analysis": self._calc_margin_analysis(raw_data),
            "12_time_index": self._calc_time_index(raw_data)
        }
        
        # 総合スコア計算（ダンスインザダーク基準）
        total_score = self._calculate_total_score(scores)

        result = {
            "horse_name": horse_name,
            "d_logic_scores": scores,
            "total_score": total_score,
            "grade": self._grade_performance(total_score),
            "data_available": True,
            "calculation_time": datetime.now().isoformat()
        }

        # キャッシュに格納
        if self._max_cache_size > 0:
            with self._cache_lock:
                if len(self._calculation_cache) >= self._max_cache_size:
                    # 最も古いエントリを削除（FIFO）
                    first_key = next(iter(self._calculation_cache), None)
                    if first_key is not None:
                        self._calculation_cache.pop(first_key, None)
                self._calculation_cache[horse_name] = result

        return result

    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を返す"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests) * 100 if total_requests else 0.0
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "cache_size": len(self._calculation_cache),
            "max_cache_size": self._max_cache_size,
            "last_loaded_at": self._last_loaded_at.isoformat() if self._last_loaded_at else None
        }

    def clear_calculation_cache(self):
        """計算キャッシュをクリア"""
        with self._cache_lock:
            self._calculation_cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def _calc_distance_aptitude(self, raw_data: Dict) -> float:
        """距離適性計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        # 距離別成績を集計
        distance_perf = {}
        for race in races:
            distance = race.get("KYORI") or race.get("distance")
            finish = race.get("KAKUTEI_CHAKUJUN") or race.get("finish")
            if distance and finish:
                if distance not in distance_perf:
                    distance_perf[distance] = []
                try:
                    distance_perf[distance].append(int(finish))
                except (ValueError, TypeError):
                    continue
        
        if not distance_perf:
            return 50.0
        
        # 平均着順から適性スコアを計算
        best_score = 0
        for distance, finishes in distance_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 10)
            best_score = max(best_score, score)
        
        return min(100, best_score)
    
    def _calc_bloodline_evaluation(self, raw_data: Dict) -> float:
        """血統評価計算"""
        stats = raw_data.get("aggregated_stats", {})
        wins = stats.get("wins", 0)
        total = stats.get("total_races", 0)
        
        if total == 0:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                total = len(races)
                wins = sum(1 for race in races if str(race.get("KAKUTEI_CHAKUJUN", race.get("finish", "99"))).strip() == "01" or race.get("KAKUTEI_CHAKUJUN", race.get("finish", 99)) == 1)
        
        win_rate = wins / total if total > 0 else 0
        return min(100, win_rate * 200)
    
    def _calc_jockey_compatibility(self, raw_data: Dict) -> float:
        """騎手相性計算"""
        jockey_perf = raw_data.get("aggregated_stats", {}).get("jockey_performance", {})
        
        if not jockey_perf:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                jockey_perf = {}
                for race in races:
                    jockey = race.get("KISHUMEI_RYAKUSHO", race.get("KISYURYAKUSYO", race.get("jockey", "")))
                    finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
                    if jockey and finish:
                        if jockey not in jockey_perf:
                            jockey_perf[jockey] = []
                        try:
                            jockey_perf[jockey].append(int(finish))
                        except (ValueError, TypeError):
                            continue
        
        if not jockey_perf:
            return 50.0
        
        best_avg = 999
        for jockey, finishes in jockey_perf.items():
            if len(finishes) >= 1:
                avg = sum(finishes) / len(finishes)
                best_avg = min(best_avg, avg)
        
        if best_avg == 999:
            return 50.0
        
        return max(0, min(100, 100 - (best_avg - 1) * 10))
    
    def _calc_trainer_evaluation(self, raw_data: Dict) -> float:
        """調教師評価計算"""
        trainer_perf = raw_data.get("aggregated_stats", {}).get("trainer_performance", {})
        
        if not trainer_perf:
            races = raw_data.get("races", raw_data.get("race_history", []))
            if races:
                trainer_perf = {}
                for race in races:
                    trainer = race.get("CHOKYOSHIMEI_RYAKUSHO", race.get("CHOUKYOUSIRYAKUSYO", race.get("trainer", "")))
                    finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
                    if trainer and finish:
                        if trainer not in trainer_perf:
                            trainer_perf[trainer] = []
                        try:
                            trainer_perf[trainer].append(int(finish))
                        except (ValueError, TypeError):
                            continue
        
        if not trainer_perf:
            return 50.0
        
        best_avg = 999
        for trainer, finishes in trainer_perf.items():
            if len(finishes) >= 1:
                avg = sum(finishes) / len(finishes)
                best_avg = min(best_avg, avg)
        
        if best_avg == 999:
            return 50.0
        
        return max(0, min(100, 100 - (best_avg - 1) * 10))
    
    def _calc_track_aptitude(self, raw_data: Dict) -> float:
        """トラック適性計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        track_perf = {}
        
        for race in races:
            track_code = race.get("TRACK_CODE", race.get("TRACKCD", race.get("track", "")))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish"))
            
            if track_code and finish:
                if track_code in ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]:
                    track = "芝"
                elif track_code in ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29"]:
                    track = "ダート"
                else:
                    track = str(track_code)
                
                if track not in track_perf:
                    track_perf[track] = []
                try:
                    track_perf[track].append(int(finish))
                except (ValueError, TypeError):
                    continue
        
        if not track_perf:
            return 50.0
        
        best_score = 0
        for track, finishes in track_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 10)
            best_score = max(best_score, score)
        
        return min(100, best_score)
    
    def _calc_weather_aptitude(self, raw_data: Dict) -> float:
        """天候適性計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        weather_perf = {}
        
        for race in races:
            tenko = race.get("TENKO_CODE", race.get("weather", 0))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            track_code = race.get("TRACK_CODE", "")
            
            if str(track_code).startswith("1"):  # 芝
                baba = race.get("SHIBA_BABAJOTAI_CODE", 1)
            else:  # ダート
                baba = race.get("DIRT_BABAJOTAI_CODE", 1)
            
            if tenko and finish:
                weather_key = f"{tenko}_{baba}"
                if weather_key not in weather_perf:
                    weather_perf[weather_key] = []
                try:
                    weather_perf[weather_key].append(int(finish))
                except (ValueError, TypeError):
                    continue
        
        if not weather_perf:
            return 50.0
        
        total_races = sum(len(finishes) for finishes in weather_perf.values())
        weighted_score = 0
        
        for weather_key, finishes in weather_perf.items():
            avg_finish = sum(finishes) / len(finishes)
            score = max(0, 100 - (avg_finish - 1) * 10)
            weight = len(finishes) / total_races
            weighted_score += score * weight
        
        return min(100, weighted_score)
    
    def _calc_popularity_factor(self, raw_data: Dict) -> float:
        """人気度要因計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        if not races:
            return 50.0
        
        performance_scores = []
        for race in races:
            popularity = race.get("TANSHO_NINKIJUN", race.get("NINKIJUN", race.get("popularity", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if popularity and finish:
                try:
                    pop_int = int(popularity)
                    fin_int = int(finish)
                    
                    if pop_int <= fin_int:
                        score = 100 - (fin_int - pop_int) * 10
                    else:
                        score = 100 - (pop_int - fin_int) * 5
                    
                    performance_scores.append(max(0, min(100, score)))
                except (ValueError, TypeError):
                    continue
        
        if not performance_scores:
            return 50.0
        
        return sum(performance_scores) / len(performance_scores)
    
    def _calc_weight_impact(self, raw_data: Dict) -> float:
        """重量影響度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        weight_scores = []
        
        for race in races:
            weight = race.get("FUTAN_JURYO", race.get("FUTAN", race.get("weight", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if weight and finish:
                try:
                    weight_int = int(weight)
                    finish_int = int(finish)
                    
                    weight_score = max(0, 100 - abs(weight_int - 550) / 10 * 5)
                    
                    if finish_int <= 3:
                        weight_score *= 1.1
                    
                    weight_scores.append(min(100, weight_score))
                except (ValueError, TypeError):
                    continue
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_horse_weight_impact(self, raw_data: Dict) -> float:
        """馬体重影響度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        weight_scores = []
        
        for race in races:
            horse_weight = race.get("BATAIJU", race.get("BATAI", race.get("horse_weight", 0)))
            weight_change = race.get("ZOGEN_SA", race.get("ZOUGEN", race.get("weight_change", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if horse_weight and finish:
                try:
                    weight_int = int(horse_weight)
                    finish_int = int(finish)
                    change_int = int(weight_change) if weight_change else 0
                    
                    base_score = 75
                    if 460 <= weight_int <= 500:
                        base_score = 100
                    elif weight_int < 440 or weight_int > 520:
                        base_score = 50
                    
                    if abs(change_int) > 10:
                        base_score *= 0.9
                    
                    weight_scores.append(base_score)
                except (ValueError, TypeError):
                    continue
        
        return sum(weight_scores) / len(weight_scores) if weight_scores else 50.0
    
    def _calc_corner_specialist(self, raw_data: Dict) -> float:
        """コーナー専門度計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        improvements = []
        
        for race in races:
            corner1 = race.get("CORNER1_JUNI", race.get("CORNER1JUN", race.get("corner1", 0)))
            corner2 = race.get("CORNER2_JUNI", race.get("CORNER2JUN", race.get("corner2", 0)))
            corner3 = race.get("CORNER3_JUNI", race.get("CORNER3JUN", race.get("corner3", 0)))
            corner4 = race.get("CORNER4_JUNI", race.get("CORNER4JUN", race.get("corner4", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            
            if finish:
                try:
                    finish_int = int(finish)
                    corners = [c for c in [corner1, corner2, corner3, corner4] if c]
                    
                    if corners:
                        last_corner = int(corners[-1])
                        improvement = last_corner - finish_int
                        
                        if improvement > 0:
                            score = 50 + improvement * 10
                        else:
                            score = 50 + improvement * 5
                        
                        improvements.append(max(0, min(100, score)))
                except (ValueError, TypeError):
                    continue
        
        return sum(improvements) / len(improvements) if improvements else 50.0
    
    def _calc_margin_analysis(self, raw_data: Dict) -> float:
        """着差分析計算"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        finish_scores = []
        
        for race in races:
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            margin = race.get("CHAKUSA", race.get("margin", ""))
            
            if finish:
                try:
                    finish_int = int(finish)
                    base_score = max(0, 100 - (finish_int - 1) * 6)
                    
                    if finish_int == 1 and margin:
                        try:
                            if "大差" in str(margin):
                                base_score = 100
                            elif margin and float(margin) >= 0.5:
                                base_score = min(100, base_score * 1.1)
                        except:
                            pass
                    
                    finish_scores.append(base_score)
                except (ValueError, TypeError):
                    continue
        
        return sum(finish_scores) / len(finish_scores) if finish_scores else 50.0
    
    def _calc_time_index(self, raw_data: Dict) -> float:
        """タイム指数計算（簡略版）"""
        races = raw_data.get("races", raw_data.get("race_history", []))
        time_scores = []
        
        for race in races:
            time = race.get("SOHA_TIME", race.get("TIME", race.get("time", 0)))
            finish = race.get("KAKUTEI_CHAKUJUN", race.get("finish", 0))
            distance = race.get("KYORI", race.get("distance", 0))
            
            if time and finish and distance:
                try:
                    time_float = float(time) / 10.0 if time else 0
                    finish_int = int(finish)
                    distance_int = int(distance)
                    
                    if time_float > 0 and distance_int > 0:
                        speed = distance_int / time_float
                        
                        base_score = 50
                        if speed > 16:
                            base_score = 90
                        elif speed > 15:
                            base_score = 75
                        elif speed > 14:
                            base_score = 60
                        
                        if finish_int <= 3:
                            base_score = min(100, base_score * 1.1)
                        
                        time_scores.append(base_score)
                except (ValueError, TypeError):
                    continue
        
        return sum(time_scores) / len(time_scores) if time_scores else 50.0
    
    def _calculate_total_score(self, scores: Dict[str, float]) -> float:
        """総合スコア計算（ダンスインザダーク基準）"""
        weights = [1.2, 1.1, 1.0, 1.0, 1.1, 0.9, 0.8, 0.9, 0.8, 1.0, 1.1, 1.2]
        
        ordered_keys = [
            "1_distance_aptitude",
            "2_bloodline_evaluation", 
            "3_jockey_compatibility",
            "4_trainer_evaluation",
            "5_track_aptitude",
            "6_weather_aptitude",
            "7_popularity_factor",
            "8_weight_impact",
            "9_horse_weight_impact",
            "10_corner_specialist_degree",
            "11_margin_analysis",
            "12_time_index"
        ]
        
        total_weighted_score = 0
        total_weight = 0
        
        for i, key in enumerate(ordered_keys):
            if key in scores:
                total_weighted_score += scores[key] * weights[i]
                total_weight += weights[i]
        
        if total_weight == 0:
            return 50.0
        
        return total_weighted_score / total_weight
    
    def _grade_performance(self, score: float) -> str:
        """成績グレード判定"""
        if score >= 90:
            return "SS (伝説級)"
        elif score >= 80:
            return "S (超一流)"
        elif score >= 70:
            return "A (一流)"
        elif score >= 60:
            return "B (良馬)"
        elif score >= 50:
            return "C (平均)"
        else:
            return "D (要改善)"

# グローバルインスタンス（シングルトン）
local_dlogic_manager_v2 = LocalDLogicRawDataManagerV2()
logger.info("🏇 地方競馬版D-LogicマネージャーV2準備完了")
