"""
V2 AI統合ハンドラー
レース限定分析とAI自然言語切り替えを実装
"""
import re
import json
import logging
import traceback
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from html import unescape
from decimal import Decimal
from services.cache_service import cache_service
from services.imlogic_engine import IMLogicEngine
from services.dlogic_raw_data_manager import DLogicRawDataManager
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
try:
    import httpx
except ImportError:
    httpx = None
import os

logger = logging.getLogger(__name__)

class V2AIHandler:
    """V2システム用のAIハンドラー"""

    COLUMN_SELECTION_PREFIX = "__COLUMN_SELECT__:"
    
    def __init__(self):
        # IMLogicEngineは毎回新規作成するため、ここでは初期化しない
        # /logic-chatと同じ動作を保証
        # DLogicRawDataManagerは血統分析で使用するため初期化
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
        self.dlogic_manager = DLogicRawDataManager()  # JRA用血統分析
        self.local_dlogic_manager = local_dlogic_manager_v2  # 地方競馬用血統分析

        # SirePerformanceAnalyzerをシングルトンで初期化（高速化）
        from services.sire_performance_analyzer import get_sire_performance_analyzer
        from services.local_sire_performance_analyzer import get_local_sire_performance_analyzer
        self.sire_analyzer = get_sire_performance_analyzer()  # JRA用
        self.local_sire_analyzer = get_local_sire_performance_analyzer()  # 地方競馬用
        logger.info("✅ SirePerformanceAnalyzer初期化完了（JRA + 地方競馬）")
        
        # N-Logicエンジン初期化
        self.nlogic_engine = None
        self.local_nlogic_engine = None
        try:
            from services.nlogic_engine import NLogicEngine
            self.nlogic_engine = NLogicEngine()
            logger.info("✅ N-Logicエンジン初期化完了")
        except Exception as e:
            logger.warning(f"⚠️ N-Logicエンジン初期化失敗（利用不可）: {e}")

        try:
            from services.local_nlogic_engine import LocalNLogicEngine
            self.local_nlogic_engine = LocalNLogicEngine()
            logger.info("✅ 地方版N-Logicエンジン初期化完了")
        except Exception as e:
            logger.warning("⚠️ 地方版N-Logicエンジン初期化失敗（利用不可）: %s", e)

        # Anthropic APIクライアント（V2では使用しないためコメントアウト）
        # self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if Anthropic else None
        self.anthropic_client = None  # V2チャットでは使用しない
        
        # 地方競馬場リスト（N-Logic地方版がカバーする競馬場）
        base_local_venues = ['川崎', '大井', '船橋', '浦和']
        if self.local_nlogic_engine:
            base_local_venues = sorted(
                set(base_local_venues) | set(self.local_nlogic_engine.LOCAL_VENUE_CODE_MAP.keys())
            )
        self.LOCAL_VENUES = base_local_venues
        
        # AI選択キーワード
        self.AI_KEYWORDS = {
            'imlogic': ['分析', '評価', 'IMLogic', 'IM', 'アイエム'],
            'viewlogic_trend': ['騎手分析', '傾向', 'トレンド', '統計', 'コース傾向', '騎手成績', '枠順'],
            'viewlogic_recommendation': ['推奨', 'おすすめ', '買い目', '馬券', '予想'],
            'viewlogic_flow': ['展開', 'ペース', '逃げ', '先行', '差し', '追込', '脚質', 'ハイペース', 'スローペース', '流れ'],
            'viewlogic_history': ['過去データ', '直近', '前走', '戦績', '成績', '最近のレース', '過去のレース', '５走', '5走', '使い方'],  # 新規追加
            'viewlogic_sire': ['種牡馬分析', '種牡馬', '父', '母父', '血統分析', '父馬', '母馬', '母父馬', 'sire', 'dam', 'broodmare'],  # 種牡馬分析サブエンジン（両方）
            'viewlogic_sire_father': ['血統父のみ', '血統父分析', '種牡馬のみ', '父馬のみ', '父だけ分析'],  # 父のみの血統分析
            'viewlogic_sire_broodmare': ['血統母父のみ', '血統母父分析', '母父のみ', '母父分析', '母父分析して', 'ブルードメアサイア', '母父だけ分析'],  # 母父のみの血統分析
            'viewlogic_data': ['データ上位', 'データ分析', 'データ抽出', '複勝率上位', '上位3頭', '上位三頭', 'トップ3'],  # データ分析サブエンジン
            'dlogic': ['d-logic', 'ディーロジック', 'D-Logic', 'Dロジック', '指数', 'スコア', '12項目', '評価点'],
            'ilogic': ['i-logic', 'ilogic', 'アイロジック', 'I-Logic', 'Iロジック', '騎手', '総合', 'レースアナリシス', 'アナリシス'],
            'nlogic': ['n-logic', 'nlogic', 'エヌロジック', 'N-Logic', 'Nロジック', 'オッズ予測', '支持率', 'レース予測', 'オッズ'],
            'flogic': ['f-logic', 'flogic', 'エフロジック', 'F-Logic', 'Fロジック', 'フェア値']
        }

    @staticmethod
    def _normalize_result_status(result: Dict[str, Any]) -> str:
        """分析結果のステータスを統一判定"""
        if result is None:
            return 'unknown'
        if result.get('has_data') is False:
            return 'no_data'
        status_raw = result.get('data_status')
        if status_raw is None:
            return 'valid'
        status = str(status_raw).lower()
        if status in ('no_data', 'missing_data', 'error', 'local_error'):
            return 'no_data'
        return 'valid'

    def _normalize_for_cache(self, value: Any) -> Any:
        """キャッシュ保存用にシリアライズ可能な形式へ正規化"""
        if isinstance(value, dict):
            items = sorted(value.items(), key=lambda item: str(item[0]))
            return {str(key): self._normalize_for_cache(val) for key, val in items}
        if isinstance(value, (set, frozenset)):
            sorted_values = sorted(list(value), key=lambda item: str(item))
            return [self._normalize_for_cache(val) for val in sorted_values]
        if isinstance(value, (list, tuple)):
            return [self._normalize_for_cache(val) for val in value]
        if isinstance(value, Decimal):
            try:
                return float(value)
            except Exception:
                return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        return str(value)

    def _build_cache_key_data(
        self,
        ai_type: str,
        race_data: Dict[str, Any],
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析種別とレース情報を基にキャッシュキー用データを生成"""
        race_id = (
            race_data.get('race_id')
            or self._derive_race_id(race_data)
            or self._derive_year_only_race_id(race_data)
            or self._derive_legacy_race_id(race_data)
        )

        key_data: Dict[str, Any] = {
            'ai_type': ai_type,
            'race_id': race_id,
            'venue': race_data.get('venue'),
            'race_number': race_data.get('race_number'),
            'race_date': str(race_data.get('race_date')) if race_data.get('race_date') is not None else None,
            'distance': str(race_data.get('distance')) if race_data.get('distance') is not None else None,
            'track_type': race_data.get('track_type'),
            'track_condition': race_data.get('track_condition'),
            'horses': sorted([str(horse) for horse in race_data.get('horses', [])])
        }

        if race_data.get('jockeys'):
            key_data['jockeys'] = [str(jockey) for jockey in race_data.get('jockeys', [])]
        if race_data.get('horse_numbers'):
            key_data['horse_numbers'] = [str(number) for number in race_data.get('horse_numbers', [])]
        if race_data.get('posts'):
            key_data['posts'] = [str(post) for post in race_data.get('posts', [])]
        if race_data.get('odds'):
            key_data['odds'] = [self._normalize_for_cache(odd) for odd in race_data.get('odds', [])]

        if extra:
            key_data['extra'] = self._normalize_for_cache(extra)

        return self._normalize_for_cache(key_data)

    def _get_cached_response(
        self,
        prefix: str,
        key_data: Dict[str, Any]
    ) -> Optional[Tuple[str, Optional[Dict[str, Any]]]]:
        """キャッシュ済みの分析結果を取得"""
        try:
            cached_payload = cache_service.get(prefix, key_data)
        except Exception as exc:
            logger.warning("キャッシュ取得エラー: prefix=%s, error=%s", prefix, exc)
            return None

        if isinstance(cached_payload, dict) and 'content' in cached_payload:
            return (
                cached_payload.get('content'),
                cached_payload.get('analysis_data')
            )
        return None

    def _save_cached_response(
        self,
        prefix: str,
        key_data: Dict[str, Any],
        content: str,
        analysis_data: Optional[Dict[str, Any]]
    ) -> None:
        """分析結果をキャッシュへ保存"""
        payload = {
            'content': content,
            'analysis_data': self._normalize_for_cache(analysis_data) if analysis_data is not None else None
        }
        try:
            cache_service.set(prefix, key_data, payload)
        except Exception as exc:
            logger.warning("キャッシュ保存エラー: prefix=%s, error=%s", prefix, exc)

    def _create_supabase_client(self):
        """Supabaseクライアントを生成"""
        from supabase import create_client

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_SERVICE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
        )

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase環境変数が設定されていません")

        return create_client(supabase_url, supabase_key)

    def _strip_html_tags(self, text: str) -> str:
        """HTMLタグを除去"""
        if not text:
            return ""

        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        return text.strip()

    def _html_to_display_text(self, html_content: str) -> str:
        """HTML本文をチャット向けに整形してテキスト化"""
        if not html_content:
            return ""

        text = html_content

        # 標準化: 改行タグやブロック要素を先に置換
        text = re.sub(r'<\s*br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*(ul|ol)\s*[^>]*>', '\n', text, flags=re.IGNORECASE)

        # 見出しや段落などは段落改行扱い
        text = re.sub(r'<\s*h[1-6][^>]*>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</\s*h[1-6]\s*>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*(p|div|section|article|header|footer|blockquote)[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</\s*(p|div|section|article|header|footer|blockquote)\s*>', '\n\n', text, flags=re.IGNORECASE)

        # リストは箇条書きへ変換
        text = re.sub(r'<\s*li[^>]*>', '\n• ', text, flags=re.IGNORECASE)
        text = re.sub(r'</\s*li\s*>', '\n', text, flags=re.IGNORECASE)

        # 残りのタグは除去
        text = re.sub(r'<[^>]+>', '', text)

        # HTMLエンティティをデコード
        text = unescape(text)

        # 余分な空白を整理
        text = text.replace('\r', '')
        text = re.sub(r'[\t\f\v]+', ' ', text)
        text = re.sub(r' *\n *', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    def _get_user_context(self, supabase, user_email: Optional[str]) -> Dict[str, Any]:
        """ユーザー情報を取得"""
        context = {
            'user_id': None,
            'is_admin': user_email in ['goldbenchan@gmail.com', 'kusanokiyoshi1@gmail.com'],
            'user_has_line': False,
            'user_points': 0
        }

        if not user_email:
            return context

        try:
            user_response = supabase.table('v2_users').select('id, line_user_id, is_line_connected').eq('email', user_email).execute()
            if user_response.data:
                user_data = user_response.data[0]
                context['user_id'] = user_data.get('id')
                line_user_id = user_data.get('line_user_id')
                is_line_connected = user_data.get('is_line_connected')
                context['user_has_line'] = bool(line_user_id) or bool(is_line_connected)

                # 追加のフォールバック: 旧LINE連携ユーザーで line_user_id が未設定の場合
                if not context['user_has_line']:
                    try:
                        v1_user_response = supabase.table('users').select('id').eq('email', user_email).single().execute()
                        if v1_user_response.data:
                            v1_user_id = v1_user_response.data.get('id')
                            ticket_response = supabase.table('line_tickets').select('is_used').eq('user_id', v1_user_id).eq('is_used', True).single().execute()
                            if ticket_response.data and ticket_response.data.get('is_used'):
                                context['user_has_line'] = True
                    except Exception as fallback_error:
                        logger.warning(f"LINE連携状態フォールバック確認中のエラー: {fallback_error}")

                points_response = supabase.table('v2_user_points').select('current_points').eq('user_id', context['user_id']).execute()
                if points_response.data:
                    context['user_points'] = points_response.data[0].get('current_points', 0)
        except Exception as e:
            logger.error(f"ユーザーコンテキスト取得エラー: {e}")

        return context

    def _fetch_race_columns(self, supabase, race_id: Optional[str]):
        """レースに紐づく公開コラムを取得"""
        if not race_id:
            return []

        try:
            response = supabase.table('v2_columns').select(
                '*, category:v2_column_categories(id, name, slug)'
            ).eq('race_id', race_id).eq('display_in_llm', True).eq('is_published', True).order('created_at', desc=True).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"コラム取得エラー: {e}")
            return []

    def _derive_race_id(self, race_data: Dict[str, Any]) -> Optional[str]:
        race_date = race_data.get('race_date')
        venue = race_data.get('venue')
        race_number = race_data.get('race_number')

        if not race_date or not venue or not race_number:
            return None

        date_str = str(race_date)
        date_digits = ''.join(filter(str.isdigit, date_str))
        if len(date_digits) < 8:
            return None

        normalized_date = date_digits[:8]

        venue_map = {
            '東京': 'tokyo', '中山': 'nakayama', '阪神': 'hanshin', '京都': 'kyoto',
            '中京': 'chukyo', '新潟': 'niigata', '福島': 'fukushima', '札幌': 'sapporo',
            '函館': 'hakodate', '小倉': 'kokura', '大井': 'ooi', '川崎': 'kawasaki',
            '浦和': 'urawa', '船橋': 'funabashi', '門別': 'monbetsu', '盛岡': 'morioka',
            '水沢': 'mizusawa', '金沢': 'kanazawa', '笠松': 'kasamatsu', '名古屋': 'nagoya',
            '園田': 'sonoda', '姫路': 'himeji', '高知': 'kochi', '佐賀': 'saga', '帯広': 'obihiro'
        }

        venue_code = venue_map.get(venue, str(venue).lower())
        return f"{normalized_date}_{venue_code}_r{race_number}"

    def _derive_year_only_race_id(self, race_data: Dict[str, Any]) -> Optional[str]:
        race_date = race_data.get('race_date')
        venue = race_data.get('venue')
        race_number = race_data.get('race_number')

        if not race_date or not venue or not race_number:
            return None

        date_str = str(race_date)
        year = ''.join(filter(str.isdigit, date_str))[:4]
        if not year:
            return None

        venue_map = {
            '東京': 'tokyo', '中山': 'nakayama', '阪神': 'hanshin', '京都': 'kyoto',
            '中京': 'chukyo', '新潟': 'niigata', '福島': 'fukushima', '札幌': 'sapporo',
            '函館': 'hakodate', '小倉': 'kokura', '大井': 'ooi', '川崎': 'kawasaki',
            '浦和': 'urawa', '船橋': 'funabashi', '門別': 'monbetsu', '盛岡': 'morioka',
            '水沢': 'mizusawa', '金沢': 'kanazawa', '笠松': 'kasamatsu', '名古屋': 'nagoya',
            '園田': 'sonoda', '姫路': 'himeji', '高知': 'kochi', '佐賀': 'saga', '帯広': 'obihiro'
        }

        venue_code = venue_map.get(venue, str(venue).lower())
        return f"{year}_{venue_code}_r{race_number}"

    def _derive_legacy_race_id(self, race_data: Dict[str, Any]) -> Optional[str]:
        race_date = race_data.get('race_date')
        venue = race_data.get('venue')
        race_number = race_data.get('race_number')

        if not race_date or not venue or not race_number:
            return None

        date_digits = str(race_date).replace('-', '')
        return f"{date_digits}-{venue}-{race_number}"

    def _get_candidate_race_ids(self, race_data: Dict[str, Any]) -> List[str]:
        candidates: List[str] = []

        for candidate in [
            race_data.get('race_id'),
            self._derive_race_id(race_data),
            self._derive_year_only_race_id(race_data),
            self._derive_legacy_race_id(race_data)
        ]:
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        return candidates

    def _build_column_selector_response(self, columns: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """複数コラム時の選択肢レスポンスを構築"""
        selector_columns = []

        for col in columns:
            actual_access_type = str(col.get('access_type') or 'free').strip() or 'free'
            selector_columns.append({
                'id': col.get('id'),
                'title': col.get('title'),
                'summary': self._strip_html_tags(col.get('summary', '')),
                'category': (col.get('category') or {}).get('name') if col.get('category') else None,
                'access_type': actual_access_type,
                'required_points': col.get('required_points'),
                'created_at': col.get('created_at')
            })

        content = (
            f"## このレースのコラム\n\n"
            f"{len(selector_columns)}件のコラムが見つかりました。閲覧したいコラムを選択してください。"
        )

        analysis_data = {
            'type': 'column_selector',
            'columns': selector_columns
        }

        return content, analysis_data

    def _render_column_content(
        self,
        column: Dict[str, Any],
        supabase,
        user_context: Dict[str, Any],
        user_email: Optional[str]
    ) -> Tuple[str, Dict[str, Any]]:
        """単一コラムの本文を生成"""

        actual_access_type = str(column.get('access_type') or 'free').strip() or 'free'

        if actual_access_type == 'free':
            access_text = '無料'
        elif actual_access_type in ['line_only', 'line_linked']:
            access_text = 'LINE連携限定'
        elif actual_access_type in ['paid', 'point_required']:
            access_text = f"{column.get('required_points', 1)}ポイント"
        else:
            access_text = f"不明({actual_access_type})"

        content_parts = [
            "## このレースのコラム",
            f"### 📝 {column.get('title')} ({access_text})"
        ]

        summary = self._strip_html_tags(column.get('summary', ''))
        if summary:
            content_parts.append(summary)

        can_access = False
        access_reason = ""
        points_consumed = False
        required_points = column.get('required_points', 1)

        if actual_access_type == 'free':
            can_access = True
        elif actual_access_type in ['line_only', 'line_linked']:
            if user_context['is_admin'] or user_context['user_has_line']:
                can_access = True
            else:
                access_reason = "📱 **このコラムの本文を読むにはLINE連携が必要です**\n\n[マイページからLINE連携を行ってください]"
        elif actual_access_type in ['paid', 'point_required']:
            if user_context['is_admin']:
                can_access = True
            elif not user_context['user_id']:
                access_reason = "⚠️ **ユーザー情報を確認できませんでした**\n\n再度ログインしてお試しください。"
            else:
                try:
                    read_check = supabase.table('v2_column_reads').select('id').eq('column_id', column['id']).eq('user_id', user_context['user_id']).execute()
                    if read_check.data:
                        can_access = True
                    elif user_context['user_points'] >= required_points:
                        new_points = user_context['user_points'] - required_points
                        supabase.table('v2_user_points').update({
                            'current_points': new_points,
                            'updated_at': datetime.now().isoformat()
                        }).eq('user_id', user_context['user_id']).execute()

                        supabase.table('v2_column_reads').insert({
                            'column_id': column['id'],
                            'user_id': user_context['user_id'],
                            'read_at': datetime.now().isoformat()
                        }).execute()

                        user_context['user_points'] = new_points
                        points_consumed = True
                        can_access = True
                    else:
                        shortage = required_points - user_context['user_points']
                        access_reason = (
                            f"💰 **このコラムの本文を読むには{required_points}ポイントが必要です**\n\n"
                            f"現在の残高: {user_context['user_points']}ポイント\n不足ポイント: {shortage}ポイント\n\n[ポイントを購入する]"
                        )
                except Exception as e:
                    logger.error(f"ポイント消費処理エラー: {e}")
                    access_reason = "⚠️ **ポイント消費処理でエラーが発生しました**\n\nしばらくしてから再度お試しください。"
        else:
            access_reason = f"⚠️ **このコラムのタイプ({actual_access_type})は認識できません**\n\n管理者にお問い合わせください。"

        if can_access:
            if actual_access_type in ['paid', 'point_required'] and not user_context['is_admin'] and points_consumed:
                content_parts.append(f"✅ **{required_points}ポイント消費しました**")
                content_parts.append("---")

            content_text = self._html_to_display_text(column.get('content', ''))
            if content_text:
                content_parts.append(content_text)
            else:
                content_parts.append("本文が未設定です。")
        else:
            content_parts.append(access_reason or "閲覧条件を満たしていないため表示できません。")

        analysis_data = {
            'type': 'column_content',
            'column_id': column.get('id'),
            'access_type': actual_access_type,
            'points_consumed': points_consumed
        }

        return "\n\n".join(content_parts), analysis_data

    def _handle_column_request(
        self,
        race_data: Dict[str, Any],
        user_email: Optional[str]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        supabase = self._create_supabase_client()
        candidate_ids = self._get_candidate_race_ids(race_data)

        columns: List[Dict[str, Any]] = []
        matched_race_id: Optional[str] = None

        for candidate in candidate_ids:
            columns = self._fetch_race_columns(supabase, candidate)
            if columns:
                matched_race_id = candidate
                break

        if not columns:
            logger.info(f"コラム未検出: race_candidates={candidate_ids}")
            return "このレースには表示できるコラムがありません。", None

        logger.info(f"コラム検出: race_id={matched_race_id}, count={len(columns)}")

        user_context = self._get_user_context(supabase, user_email)

        if len(columns) == 1:
            column_content, analysis_data = self._render_column_content(columns[0], supabase, user_context, user_email)
            return column_content, analysis_data

        content, analysis_data = self._build_column_selector_response(columns)
        return content, analysis_data

    def _handle_column_selection(
        self,
        race_data: Dict[str, Any],
        user_email: Optional[str],
        selection_id: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        supabase = self._create_supabase_client()
        try:
            column_response = supabase.table('v2_columns').select(
                '*, category:v2_column_categories(id, name, slug)'
            ).eq('id', selection_id).eq('display_in_llm', True).eq('is_published', True).single().execute()
        except Exception as e:
            logger.error(f"コラム選択エラー: {e}")
            return "選択したコラムを取得できませんでした。", None

        if not column_response.data:
            return "選択したコラムが見つかりませんでした。", None

        column = column_response.data

        candidate_ids = self._get_candidate_race_ids(race_data)

        if column.get('race_id') and candidate_ids and column.get('race_id') not in candidate_ids:
            return "このチャットでは選択できないコラムです。", None

        user_context = self._get_user_context(supabase, user_email)
        return self._render_column_content(column, supabase, user_context, user_email)
    
        
    def determine_ai_type(self, message: str) -> Tuple[str, str]:
        """
        メッセージからAIタイプを判定

        Returns:
            (ai_type, sub_type) のタプル
        """

        message_lower = message.lower()

        # コラム表示の判定（最優先）
        if 'コラム' in message and ('表示' in message or '見せて' in message or '見る' in message or 'を教えて' in message):
            return ('column', 'display')

        # 特定のAIキーワードを最優先で判定（他のキーワードより優先）
        # MetaLogic分析（メタ予想システム - 最優先）
        if 'metalogic' in message_lower or 'meta-logic' in message_lower or 'メタロジック' in message or 'メタ予想' in message or 'メタログic' in message:
            return ('metalogic', 'analysis')
        
        # F-Logic分析（明示的な指定を最優先）
        if 'f-logic' in message_lower or 'flogic' in message_lower or 'エフロジック' in message or 'フェア値' in message:
            return ('flogic', 'analysis')
        
        # D-Logic分析（明示的な指定を優先）
        if 'd-logic' in message_lower or 'dlogic' in message_lower or 'ディーロジック' in message:
            return ('dlogic', 'analysis')
        
        # IMLogic分析（明示的な指定を優先）
        if 'imlogic' in message_lower or 'アイエムロジック' in message:
            return ('imlogic', 'analysis')
        
        # 「馬70騎手30」などのIMLogic特有のパターン
        if '馬' in message and '騎手' in message and ('％' in message or '%' in message or '分析' in message):
            return ('imlogic', 'analysis')
        
        # ViewLogic５走の使い方案内（最優先）
        if '使い方' in message and ('ViewLogic' in message or 'viewlogic' in message_lower or '５走' in message or '5走' in message):
            return ('viewlogic', 'history')
        
        # ViewLogic過去データ（馬名・騎手名が含まれる場合を優先）
        # レースデータから馬名と騎手名を取得して判定に使用
        if hasattr(self, 'current_race_data'):
            horses = self.current_race_data.get('horses', [])
            jockeys = self.current_race_data.get('jockeys', [])
            
            # 馬名が含まれているかチェック
            for horse in horses:
                if horse in message:
                    # 過去データ関連のキーワードがあれば過去データと判定
                    for keyword in self.AI_KEYWORDS['viewlogic_history']:
                        if keyword in message_lower:
                            return ('viewlogic', 'history')
                    # 馬名だけでも反応（ただし明示的な他のキーワードがない場合）
                    # ※「データ」「血統」は除外（傾向分析や血統分析の可能性があるため）
                    if not any(kw in message_lower for kw_list in [
                        self.AI_KEYWORDS['dlogic'], 
                        self.AI_KEYWORDS['imlogic'],
                        self.AI_KEYWORDS['ilogic'],
                        self.AI_KEYWORDS['viewlogic_flow'],
                        self.AI_KEYWORDS['viewlogic_recommendation'],
                        self.AI_KEYWORDS['viewlogic_sire']
                    ] for kw in kw_list):
                        return ('viewlogic', 'history')
            
            # 騎手名が含まれているかチェック（部分一致と短縮名対応）
            for jockey in jockeys:
                if jockey:
                    # フルネームでの一致
                    if jockey in message:
                        for keyword in self.AI_KEYWORDS['viewlogic_history']:
                            if keyword in message_lower:
                                return ('viewlogic', 'history')
                        # 騎手名だけでも反応
                        if not any(kw in message_lower for kw_list in [
                            self.AI_KEYWORDS['dlogic'], 
                            self.AI_KEYWORDS['imlogic'],
                            self.AI_KEYWORDS['ilogic'],
                            self.AI_KEYWORDS['viewlogic_flow'],
                            self.AI_KEYWORDS['viewlogic_recommendation'],
                            self.AI_KEYWORDS['viewlogic_sire']
                        ] for kw in kw_list):
                            return ('viewlogic', 'history')
                    
                    # 短縮名での一致（例：川田将雅 → 川田、C.ルメール → ルメール）
                    if len(jockey) >= 2:
                        short_name = jockey[:2]  # 最初の2文字
                        if short_name in message:
                            for keyword in self.AI_KEYWORDS['viewlogic_history']:
                                if keyword in message_lower:
                                    return ('viewlogic', 'history')
                            # 短縮名だけでも反応
                            if not any(kw in message_lower for kw_list in [
                                self.AI_KEYWORDS['dlogic'], 
                                self.AI_KEYWORDS['imlogic'],
                                self.AI_KEYWORDS['ilogic'],
                                self.AI_KEYWORDS['viewlogic_flow'],
                                self.AI_KEYWORDS['viewlogic_recommendation'],
                                self.AI_KEYWORDS['viewlogic_sire']
                            ] for kw in kw_list):
                                return ('viewlogic', 'history')
                    
                    # 外国人騎手の場合（C.ルメール → ルメール）
                    if '.' in jockey:
                        last_part = jockey.split('.')[-1]
                        if last_part in message:
                            for keyword in self.AI_KEYWORDS['viewlogic_history']:
                                if keyword in message_lower:
                                    return ('viewlogic', 'history')
                            if not any(kw in message_lower for kw_list in [
                                self.AI_KEYWORDS['dlogic'], 
                                self.AI_KEYWORDS['imlogic'],
                                self.AI_KEYWORDS['ilogic'],
                                self.AI_KEYWORDS['viewlogic_flow'],
                                self.AI_KEYWORDS['viewlogic_recommendation'],
                                self.AI_KEYWORDS['viewlogic_sire']
                            ] for kw in kw_list):
                                return ('viewlogic', 'history')

        # ViewLogic父のみの血統分析（最優先）
        for keyword in self.AI_KEYWORDS['viewlogic_sire_father']:
            if keyword in message_lower or keyword in message:
                return ('viewlogic', 'sire_father')

        # ViewLogic母父のみの血統分析（優先）
        for keyword in self.AI_KEYWORDS['viewlogic_sire_broodmare']:
            if keyword in message_lower or keyword in message:
                return ('viewlogic', 'sire_broodmare')

        # ViewLogic種牡馬分析（優先度高）
        for keyword in self.AI_KEYWORDS['viewlogic_sire']:
            if keyword in message_lower or keyword in message:  # 「父」「母父」は漢字なのでmessageでも確認
                return ('viewlogic', 'sire')

        # ViewLogic展開予想（優先度高）
        for keyword in self.AI_KEYWORDS['viewlogic_flow']:
            if keyword in message_lower:
                return ('viewlogic', 'flow')
        
        # ViewLogicデータ分析（上位3頭抽出）
        for keyword in self.AI_KEYWORDS['viewlogic_data']:
            if keyword in message_lower:
                return ('viewlogic', 'data')
        
        # ViewLogic傾向分析（I-Logicより優先）
        for keyword in self.AI_KEYWORDS['viewlogic_trend']:
            if keyword in message_lower:
                return ('viewlogic', 'trend')
        
        # F-Logic分析（投資価値判定）
        for keyword in self.AI_KEYWORDS['flogic']:
            if keyword.lower() in message_lower:
                return ('flogic', 'analysis')
        
        # I-Logic分析
        for keyword in self.AI_KEYWORDS['ilogic']:
            if keyword.lower() in message_lower:
                return ('ilogic', 'analysis')
        
        # N-Logic（オッズ予測）
        for keyword in self.AI_KEYWORDS['nlogic']:
            if keyword.lower() in message_lower:
                return ('nlogic', 'prediction')
        
        # ViewLogic推奨
        for keyword in self.AI_KEYWORDS['viewlogic_recommendation']:
            if keyword in message_lower:
                return ('viewlogic', 'recommendation')
        
        # その他のD-Logicキーワード
        for keyword in self.AI_KEYWORDS['dlogic']:
            if keyword.lower() in message_lower:
                return ('dlogic', 'analysis')
        
        # その他のIMLogicキーワード
        for keyword in self.AI_KEYWORDS['imlogic']:
            if keyword.lower() in message_lower:
                return ('imlogic', 'analysis')
        
        # 「標準分析」はD-Logicとして扱う
        if '標準' in message_lower and '分析' in message_lower:
            return ('dlogic', 'analysis')
        
        # デフォルトはIMLogic分析
        return ('imlogic', 'analysis')
    
    def create_race_context_prompt(self, race_data: Dict[str, Any]) -> str:
        """
        レース限定のコンテキストプロンプトを生成
        """
        horses_list = race_data.get('horses', [])
        horses_str = '、'.join(horses_list) if horses_list else '情報なし'
        
        prompt = f"""
あなたは競馬予想の専門AIです。以下のレースについてのみ分析・回答してください。

【対象レース情報】
- 開催日: {race_data.get('race_date', '不明')}
- 開催場: {race_data.get('venue', '不明')}
- レース番号: {race_data.get('race_number', '不明')}R
- レース名: {race_data.get('race_name', '不明')}
- 距離: {race_data.get('distance', '不明')}
- 馬場状態: {race_data.get('track_condition', '不明')}
- 出走馬: {horses_str}

【重要な制約】
1. 上記レース以外の情報や分析は一切行わないでください
2. 他のレースについて聞かれても「このチャットは{race_data.get('venue')} {race_data.get('race_number')}R専用です」と回答
3. 出走馬リストにない馬については分析できません
4. レース当日の最新情報（オッズ、馬体重等）は持っていません
"""
        return prompt
    
    def _is_local_racing(self, venue: str) -> bool:
        """地方競馬場かどうかを判定"""
        return venue in self.LOCAL_VENUES

    def _normalize_track_type(self, track_type: Optional[str]) -> Optional[str]:
        if not track_type:
            return None
        if isinstance(track_type, str):
            normalized = track_type.strip()
            if not normalized:
                return None
            lower = normalized.lower()
            if '芝' in normalized or 'turf' in lower:
                return '芝'
            if 'ダート' in normalized or '砂' in normalized or 'dirt' in lower:
                return 'ダート'
            if '障害' in normalized or 'steeple' in lower:
                return '障害'
        return None
    
    async def process_imlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[Dict]]:
        """
        IMLogicメッセージ処理（地方競馬対応版）
        """
        try:
            # 分析を実行する場合
            if self._should_analyze(message):
                venue = race_data.get('venue', '')
                
                # 地方競馬場の場合は地方競馬版エンジンを使用
                if self._is_local_racing(venue):
                    from services.local_imlogic_engine_v2 import local_imlogic_engine_v2
                    imlogic_engine_temp = local_imlogic_engine_v2
                    logger.info(f"🏇 地方競馬版IMLogicエンジンを使用: {venue}")
                else:
                    # JRA版（既存）
                    from services.imlogic_engine import get_imlogic_engine
                    imlogic_engine_temp = get_imlogic_engine()
                    logger.info(f"🏇 JRA版IMLogicエンジンを使用: {venue}")
                
                # デフォルトの設定を使用（設定が無い場合）
                if not settings:
                    settings = self._get_default_imlogic_settings()
                
                # IMLogicEngineで分析
                # フロントエンドからのデータ構造に対応
                # 0も有効な値として扱うため、Noneチェックを使用
                if 'horse_weight' in settings:
                    horse_weight = settings['horse_weight']
                elif 'horse_ratio' in settings:
                    horse_weight = settings['horse_ratio']
                else:
                    horse_weight = 70
                    
                if 'jockey_weight' in settings:
                    jockey_weight = settings['jockey_weight']
                elif 'jockey_ratio' in settings:
                    jockey_weight = settings['jockey_ratio']
                else:
                    jockey_weight = 30
                raw_weights = settings.get('item_weights') or settings.get('weights', {})
                
                # フロントエンドのキー形式が番号付きか番号なしかを判定
                if '1_distance_aptitude' in raw_weights:
                    # すでに番号付き形式
                    item_weights = raw_weights
                elif 'distance_aptitude' in raw_weights:
                    # 番号なし形式から番号付き形式に変換
                    item_weights = {
                        '1_distance_aptitude': raw_weights.get('distance_aptitude', 8.33),
                        '2_bloodline_evaluation': raw_weights.get('bloodline_evaluation', 8.33),
                        '3_jockey_compatibility': raw_weights.get('jockey_compatibility', 8.33),
                        '4_trainer_evaluation': raw_weights.get('trainer_evaluation', 8.33),
                        '5_track_aptitude': raw_weights.get('track_aptitude', 8.33),
                        '6_weather_aptitude': raw_weights.get('weather_aptitude', 8.33),
                        '7_popularity_factor': raw_weights.get('popularity_factor', 8.33),
                        '8_weight_impact': raw_weights.get('weight_impact', 8.33),
                        '9_horse_weight_impact': raw_weights.get('horse_weight_impact', 8.33),
                        '10_corner_specialist': raw_weights.get('corner_specialist', 8.33),
                        '11_margin_analysis': raw_weights.get('margin_analysis', 8.33),
                        '12_time_index': raw_weights.get('time_index', 8.37)
                    }
                else:
                    # デフォルト値を使用
                    item_weights = {
                        '1_distance_aptitude': 8.33,
                        '2_bloodline_evaluation': 8.33,
                        '3_jockey_compatibility': 8.33,
                        '4_trainer_evaluation': 8.33,
                        '5_track_aptitude': 8.33,
                        '6_weather_aptitude': 8.33,
                        '7_popularity_factor': 8.33,
                        '8_weight_impact': 8.33,
                        '9_horse_weight_impact': 8.33,
                        '10_corner_specialist': 8.33,
                        '11_margin_analysis': 8.33,
                        '12_time_index': 8.37
                    }
                
                cache_extra = {
                    'horse_weight': horse_weight,
                    'jockey_weight': jockey_weight,
                    'item_weights': item_weights
                }
                cache_key_data = self._build_cache_key_data(
                    ai_type='nar_imlogic',
                    race_data=race_data,
                    extra=cache_extra
                )
                cached_response = self._get_cached_response('imlogic_analysis', cache_key_data)
                if cached_response:
                    return cached_response

                # 一時的なエンジンインスタンスで分析
                logger.info(f"IMLogic分析開始 - venue: {venue}, horses: {race_data.get('horses', [])}")
                logger.info(f"IMLogic重み設定 - horse: {horse_weight}%, jockey: {jockey_weight}%")
                
                analysis_result = imlogic_engine_temp.analyze_race(
                    race_data=race_data,
                    horse_weight=horse_weight,
                    jockey_weight=jockey_weight,
                    item_weights=item_weights
                )
                if isinstance(analysis_result, dict):
                    analysis_result.setdefault('race_snapshot', race_data)
                    race_info = analysis_result.get('race_info') or {
                        'venue': race_data.get('venue', ''),
                        'race_number': race_data.get('race_number', ''),
                        'race_name': race_data.get('race_name', '')
                    }
                    analysis_result['race_info'] = race_info

                    results_payload = analysis_result.get('results')
                    if not results_payload and 'rankings' in analysis_result and isinstance(analysis_result['rankings'], list):
                        results_payload = analysis_result['rankings']
                    if results_payload is not None:
                        analysis_result['results'] = results_payload

                    if 'scores' not in analysis_result and isinstance(results_payload, list):
                        analysis_result['scores'] = results_payload
                
                logger.info(f"IMLogic分析結果: status={analysis_result.get('status')}, results数={len(analysis_result.get('results', []))}")
                
                # 結果が空の場合のチェック（'scores'と'results'の両方をチェック）
                if not analysis_result or (not analysis_result.get('scores') and not analysis_result.get('results')):
                    logger.error(f"IMLogic分析結果が空: {analysis_result}")
                    logger.error(f"race_data詳細: {race_data}")
                    return ("分析に失敗しました。馬名が正しいか確認してください。", None)
                
                # 結果のフォーマット
                formatted_content = self._format_imlogic_result(analysis_result, race_data)
                self._save_cached_response(
                    'imlogic_analysis',
                    cache_key_data,
                    formatted_content,
                    analysis_result
                )
                return (formatted_content, analysis_result)
            
            # 通常の会話の場合
            else:
                # レースコンテキストを設定
                race_context = self.create_race_context_prompt(race_data)
                
                # IMLogicの設定説明
                if settings:
                    imlogic_prompt = self._create_imlogic_prompt(settings)
                else:
                    imlogic_prompt = """
IMLogicは、ユーザーがカスタマイズ可能な分析システムです。
馬と騎手の比率、12項目の重み付けを自由に設定できます。
"""
                
                # Claude APIを呼び出し（会話用）
                if self.anthropic_client:
                    full_prompt = f"{race_context}\n\n{imlogic_prompt}\n\nユーザーの質問: {message}"
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=2000,
                        temperature=0.7,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ]
                    )
                    return (response.content[0].text, None)
                else:
                    return ("会話機能は現在利用できません", None)
            
        except Exception as e:
            import traceback
            logger.error(f"IMLogic処理エラー: {e}")
            logger.error(f"IMLogicスタックトレース: {traceback.format_exc()}")
            logger.error(f"IMLogicエラー時のrace_data: {race_data}")
            return (f"申し訳ございません。IMLogic分析中にエラーが発生しました: {str(e)}", None)
    
    def _should_analyze(self, message: str) -> bool:
        """メッセージが分析要求かどうかを判定"""
        analyze_keywords = ['分析', '評価', '順位', '上位', '予想', 'ランキング', 'スコア', '計算']
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in analyze_keywords)
    
    def _get_default_imlogic_settings(self) -> Dict[str, Any]:
        """デフォルトのIMLogic設定を返す"""
        return {
            'horse_ratio': 70,
            'jockey_ratio': 30,
            'weights': self._get_default_weights()
        }
    
    def _get_default_weights(self) -> Dict[str, float]:
        """デフォルトの12項目重み付けを返す"""
        return {
            '1_distance_aptitude': 8.33,
            '2_bloodline_evaluation': 8.33,
            '3_jockey_compatibility': 8.33,
            '4_trainer_evaluation': 8.33,
            '5_track_aptitude': 8.33,
            '6_weather_aptitude': 8.33,
            '7_popularity_factor': 8.33,
            '8_weight_impact': 8.33,
            '9_horse_weight_impact': 8.33,
            '10_corner_specialist': 8.33,
            '11_margin_analysis': 8.33,
            '12_time_index': 8.37
        }
    
    def _format_imlogic_result(self, analysis_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """IMLogic分析結果をフォーマット"""
        try:
            # 'scores'と'results'の両方に対応
            scores = analysis_result.get('scores') or analysis_result.get('results', [])
            if not scores:
                return "分析結果が取得できませんでした。"
            
            # スコア順にソート（Noneの場合は-1として扱う）
            scores.sort(key=lambda x: x.get('total_score') if x.get('total_score') is not None else -1, reverse=True)
            
            # 結果のフォーマット
            lines = []
            lines.append(f"🎯 IMLogic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R")
            lines.append("")
            
            # 全頭を順位付きで表示（I-Logic形式）
            emojis = ['🥇', '🥈', '🥉']
            # データ不足（None）の馬を除外、マイナススコアは有効
            valid_scores = [
                s for s in scores
                if s.get('total_score') is not None and self._normalize_result_status(s) == 'valid'
            ]
            no_data_scores = [
                s for s in scores
                if self._normalize_result_status(s) == 'no_data'
            ]

            if not valid_scores:
                valid_scores = [s for s in scores if s.get('total_score') is not None]
            
            for i, score_data in enumerate(valid_scores):
                rank_value = score_data.get('rank')
                if not isinstance(rank_value, (int, float)) or rank_value <= 0:
                    rank_value = i + 1
                # 上位3位まで絵文字、4位以降は数字表示
                if i < 3:
                    rank_display = f"{emojis[i]} {int(rank_value)}位:"
                else:
                    rank_display = f"{int(rank_value)}位:"
                
                # 'horse_name'と'horse'の両方に対応
                horse_name = score_data.get('horse_name') or score_data.get('horse', '不明')
                total_score = score_data.get('total_score', 0)
                horse_score = score_data.get('horse_score', 0)
                jockey_score = score_data.get('jockey_score', 0)
                
                lines.append(f"{rank_display} {horse_name}: {total_score:.1f}点")
                lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
                
                # 次の馬との間に空行を追加（最後の馬以外）
                if i < len(valid_scores) - 1:
                    lines.append("")
                
                # 6位目に区切り線を追加
                if i == 5:
                    lines.append("【6位以下】")
            
            # データがない馬がいる場合の注記
            if no_data_scores:
                no_data_horses = [s.get('horse_name') or s.get('horse', '不明') for s in no_data_scores]
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータベースにデータがありません: {', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"結果フォーマットエラー: {e}")
            return "分析結果の表示中にエラーが発生しました。"
    
    async def process_metalogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        MetaLogicメッセージ処理（メタ予想システム）
        I-Logic 40%, D-Logic 30%, ViewLogic 30%の重み付けアンサンブル
        
        Returns:
            (content, analysis_data) のタプル
        """
        try:
            venue = race_data.get('venue')
            cache_key_data = None
            if self._is_local_racing(venue):
                from services.local_metalogic_engine_v2 import local_metalogic_engine_v2
                metalogic_engine_instance = local_metalogic_engine_v2
                logger.info("MetaLogic: 地方競馬版エンジンを使用 (%s)", venue)
                cache_key_data = self._build_cache_key_data(
                    ai_type='nar_metalogic',
                    race_data=race_data,
                    extra={'odds': race_data.get('odds')}
                )
                cached_response = self._get_cached_response('metalogic_analysis', cache_key_data)
                if cached_response:
                    return cached_response
                analysis_result = metalogic_engine_instance.analyze_race(race_data)
            else:
                from services.metalogic_engine import metalogic_engine
                logger.info("MetaLogic: JRA版エンジンを使用 (%s)", venue)
                analysis_result = await metalogic_engine.analyze_race(race_data)
            
            if analysis_result.get('status') != 'success':
                return (analysis_result.get('message', '分析に失敗しました'), None)
            
            # 結果のフォーマット
            content = self._format_metalogic_result(analysis_result)
            
            if cache_key_data is not None:
                self._save_cached_response(
                    'metalogic_analysis',
                    cache_key_data,
                    content,
                    analysis_result
                )

            return (content, analysis_result)
            
        except Exception as e:
            logger.error(f"MetaLogic処理エラー: {e}")
            traceback.print_exc()
            return ("MetaLogicの分析中にエラーが発生しました。", None)
    
    def _format_metalogic_result(self, result: Dict[str, Any]) -> str:
        """MetaLogic結果のフォーマット"""
        try:
            rankings = result.get('rankings', [])
            
            if not rankings:
                return "分析結果がありません。"
            
            content = "🎯 **MetaLogic メタ予想システム**\n"
            content += "（I-Logic 40% + D-Logic 30% + ViewLogic 30% + 市場評価）\n\n"
            content += "**推奨馬（メタスコア順）**\n\n"
            
            for item in rankings[:5]:
                horse = item.get('horse', '不明')
                score = item.get('meta_score', 0)
                details = item.get('details', {})
                
                # 信頼度インジケーター
                if details.get('engine_count', 0) >= 3:
                    confidence = "⭐⭐⭐"
                elif details.get('engine_count', 0) >= 2:
                    confidence = "⭐⭐"
                else:
                    confidence = "⭐"
                
                content += f"**{item.get('rank')}位 {horse}** {confidence}\n"
                content += f"  メタスコア: **{score:.1f}点**\n"
                content += f"  - D-Logic: {details.get('d_logic', 0):.1f}点\n"
                content += f"  - I-Logic: {details.get('i_logic', 0):.1f}点\n"
                content += f"  - ViewLogic: {details.get('view_logic', 0):.1f}点\n"
                content += f"  - オッズ評価: {details.get('odds_factor', 0):.1f}点\n\n"
            
            content += "\n💡 **解説**\n"
            content += "MetaLogicは3つのAIエンジンと市場評価を統合した\n"
            content += "アンサンブル予想システムです。\n"
            content += "I-Logicの高精度を活かしつつ、複数視点での検証により\n"
            content += "安定性を向上させています。\n"
            
            return content
            
        except Exception as e:
            logger.error(f"MetaLogic結果フォーマットエラー: {e}")
            return "結果の表示中にエラーが発生しました。"
    
    async def process_viewlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        sub_type: str = 'trend'
    ) -> Tuple[str, Optional[Dict]]:
        """
        ViewLogicメッセージ処理（地方競馬対応版）
        
        Returns:
            (content, analysis_data) のタプル
        """
        try:
            venue = race_data.get('venue', '不明')
            race_number = race_data.get('race_number', '不明')
            
            # 地方競馬場の場合は地方競馬版エンジンを使用
            is_local_racing = self._is_local_racing(venue)
            if is_local_racing:
                from services.local_viewlogic_engine_v2 import local_viewlogic_engine_v2
                viewlogic_engine = local_viewlogic_engine_v2
                logger.info(f"🏇 地方競馬版ViewLogicエンジンを使用: {venue}")
            else:
                # JRA版（既存）
                from services.viewlogic_engine import ViewLogicEngine
                viewlogic_engine = ViewLogicEngine()
                logger.info(f"🏇 JRA版ViewLogicエンジンを使用: {venue}")
            
            if sub_type == 'flow':
                cache_key_data = None
                if is_local_racing:
                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_viewlogic',
                        race_data=race_data,
                        extra={'sub_type': 'flow'}
                    )
                    cached_response = self._get_cached_response('viewlogic_flow', cache_key_data)
                    if cached_response:
                        return cached_response

                # 展開予想（高度な分析版を使用）
                logger.info(f"ViewLogic展開予想開始: venue={venue}, horses={race_data.get('horses', [])}")
                result = viewlogic_engine.predict_race_flow_advanced(race_data)
                logger.info(f"ViewLogic展開予想結果: status={result.get('status')}, type={result.get('type')}")
                
                if result.get('status') == 'success':
                    # 外部フォーマット関数を使用
                    from services.v2.ai_handler_format_advanced import format_flow_prediction_advanced
                    content = format_flow_prediction_advanced(result)
                    if cache_key_data is not None:
                        self._save_cached_response(
                            'viewlogic_flow',
                            cache_key_data,
                            content,
                            result
                        )
                    return (content, result)
                else:
                    logger.error(f"ViewLogic展開予想エラー詳細: {result}")
                    return (f"展開予想に失敗しました: {result.get('message', '不明なエラー')}", None)
                    
            elif sub_type == 'trend':
                cache_key_data = None
                if is_local_racing:
                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_viewlogic',
                        race_data=race_data,
                        extra={'sub_type': 'trend'}
                    )
                    cached_response = self._get_cached_response('viewlogic_trend', cache_key_data)
                    if cached_response:
                        return cached_response

                # コース傾向分析（実際の出場馬・騎手データを使用）
                import signal
                import time
                
                # タイムアウトハンドラー
                def timeout_handler(signum, frame):
                    raise TimeoutError("傾向分析がタイムアウトしました")
                
                try:
                    # 25秒のタイムアウトを設定（Renderの30秒制限より短く）
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(25)
                    
                    result = viewlogic_engine.analyze_course_trend(race_data)
                    
                    # タイムアウトをリセット
                    signal.alarm(0)
                    
                    if result['status'] == 'success':
                        content = self._format_trend_analysis(result)
                        if cache_key_data is not None:
                            self._save_cached_response(
                                'viewlogic_trend',
                                cache_key_data,
                                content,
                                result
                            )
                        return (content, result)
                    else:
                        return (f"傾向分析に失敗しました: {result.get('message', '不明なエラー')}", None)
                        
                except TimeoutError:
                    signal.alarm(0)  # タイムアウトをリセット
                    logger.error("ViewLogic傾向分析がタイムアウトしました（25秒）")
                    return ("傾向分析の処理に時間がかかりすぎています。データ量が多い可能性があります。", None)
                except Exception as e:
                    signal.alarm(0)  # タイムアウトをリセット
                    logger.error(f"ViewLogic傾向分析中にエラー: {e}")
                    return (f"傾向分析中にエラーが発生しました: {str(e)}", None)
                    
            elif sub_type == 'recommendation':
                cache_key_data = None
                if is_local_racing:
                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_viewlogic',
                        race_data=race_data,
                        extra={'sub_type': 'recommendation'}
                    )
                    cached_response = self._get_cached_response('viewlogic_recommendation', cache_key_data)
                    if cached_response:
                        return cached_response

                # 推奨馬券（馬券推奨として実装）
                result = viewlogic_engine.recommend_betting_tickets(
                    race_data=race_data
                )
                
                if result['status'] == 'success':
                    content = self._format_betting_recommendations(result)
                    if cache_key_data is not None:
                        self._save_cached_response(
                            'viewlogic_recommendation',
                            cache_key_data,
                            content,
                            result
                        )
                    return (content, result)
                else:
                    # フォールバック: 基本的な推奨を提供
                    return (f"""
🎯 ViewLogic推奨馬券
{venue} {race_number}R

申し訳ございません。現在、推奨馬券の生成ができません。
以下の分析機能をご利用ください：

• 「展開予想」- レースの流れを予想
• 「傾向分析」- コース・騎手成績を分析

これらの結果を参考に馬券をご検討ください。
""", None)
            
            elif sub_type == 'history':
                # 使い方案内の判定
                if '使い方' in message or 'ViewLogic５走の使い方' in message:
                    return self._get_viewlogic_5race_guide(race_data), None
                
                # 過去データ表示（新機能）
                # メッセージから馬名または騎手名を抽出
                horses = race_data.get('horses', [])
                jockeys = race_data.get('jockeys', [])
                
                # 馬名チェック
                target_horse = None
                logger.info(f"ViewLogic過去データ: 馬名マッチング開始 horses={horses}, message={message}")
                for horse in horses:
                    if horse in message:
                        target_horse = horse
                        logger.info(f"ViewLogic過去データ: 馬名マッチ成功 target_horse={target_horse}")
                        break
                
                # 騎手名チェック
                target_jockey = None
                if not target_horse:
                    for jockey in jockeys:
                        if jockey and jockey in message:
                            target_jockey = jockey
                            break
                
                cache_key_data = None
                if is_local_racing and (target_horse or target_jockey):
                    cache_extra = {
                        'sub_type': 'history'
                    }
                    if target_horse:
                        cache_extra['target_horse'] = target_horse
                    if target_jockey:
                        cache_extra['target_jockey'] = target_jockey
                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_viewlogic',
                        race_data=race_data,
                        extra=cache_extra
                    )
                    cached_response = self._get_cached_response('viewlogic_history', cache_key_data)
                    if cached_response:
                        return cached_response

                # プログレスバー表示用のメッセージを最初に返す
                if target_horse:
                    progress_message = "ViewLogic過去データを取得中...\n" + target_horse + "の履歴を検索しています..."
                elif target_jockey:
                    progress_message = "ViewLogic過去データを取得中...\n" + target_jockey + "騎手の履歴を検索しています..."
                else:
                    return ("分析対象の馬名または騎手名が見つかりませんでした。", None)
                
                # 実際のデータ取得処理
                if target_horse:
                    # 馬の過去データ取得
                    logger.info(f"ViewLogic過去データ: 馬データ取得開始 target_horse={target_horse}, engine={type(viewlogic_engine).__name__}")
                    result = viewlogic_engine.get_horse_history(target_horse)
                    logger.info(f"ViewLogic過去データ: 馬データ取得結果 status={result.get('status')}, message={result.get('message', 'N/A')}")
                    if result['status'] == 'success':
                        content = self._format_horse_history(result, target_horse)
                        # プログレスメッセージと実際のコンテンツを結合
                        full_content = f"{progress_message}\n\n{content}"
                        if cache_key_data is not None:
                            self._save_cached_response(
                                'viewlogic_history',
                                cache_key_data,
                                full_content,
                                result
                            )
                        return (full_content, result)
                    else:
                        return (f"{progress_message}\n\n{target_horse}の過去データが見つかりませんでした。", None)
                
                elif target_jockey:
                    # 騎手の過去データ取得
                    result = viewlogic_engine.get_jockey_history(target_jockey)
                    if result['status'] == 'success':
                        content = self._format_jockey_history(result, target_jockey)
                        # プログレスメッセージと実際のコンテンツを結合
                        full_content = f"{progress_message}\n\n{content}"
                        if cache_key_data is not None:
                            self._save_cached_response(
                                'viewlogic_history',
                                cache_key_data,
                                full_content,
                                result
                            )
                        return (full_content, result)
                    else:
                        return (f"{progress_message}\n\n{target_jockey}騎手の過去データが見つかりませんでした。", None)
                
                else:
                    # 馬名も騎手名も見つからない場合
                    example_horse = horses[0] if horses else 'ドウデュース'
                    return (f"出走馬または騎手の名前を指定してください。例：「{example_horse}の過去データ」", None)

            elif sub_type == 'sire':
                # 種牡馬分析（父と母父両方）
                return self._generate_sire_analysis(race_data, mode='both')

            elif sub_type == 'sire_father':
                # 父のみの血統分析
                return self._generate_sire_analysis(race_data, mode='father')

            elif sub_type == 'sire_broodmare':
                # 母父のみの血統分析
                return self._generate_sire_analysis(race_data, mode='broodmare')

            elif sub_type == 'data':
                # データ分析（上位3頭抽出）
                return self._generate_data_analysis(race_data)

            else:
                return ("ViewLogic機能をご利用いただきありがとうございます。「展開」「傾向」「推奨」のいずれかをお試しください。", None)
                
        except ImportError as e:
            logger.error(f"ViewLogicエンジンのインポートエラー: {e}")
            return ("ViewLogicエンジンの読み込みに失敗しました。システム管理者にお問い合わせください。", None)
        except Exception as e:
            import traceback
            logger.error(f"ViewLogic処理エラー: {e}")
            logger.error(f"ViewLogicスタックトレース: {traceback.format_exc()}")
            logger.error(f"ViewLogicエラー時のrace_data: {race_data}")
            logger.error(f"ViewLogicエラー時のsub_type: {sub_type}")
            return (f"ViewLogic分析中にエラーが発生しました: {str(e)}", None)
    
    def _format_flow_prediction(self, result: Dict[str, Any]) -> str:
        """展開予想結果をフォーマット（高度な分析版対応）"""
        lines = []
        lines.append("🏇 **ViewLogic展開予想**")
        
        # レース情報
        race_info = result.get('race_info', {})
        lines.append(f"{race_info.get('venue', '')} {race_info.get('race_number', '')}R - {race_info.get('race_name', '')}")
        if race_info.get('distance'):
            lines.append(f"距離: {race_info.get('distance', '')}")
        lines.append("")
        
        # 新形式（predict_race_flow_advanced）の場合
        if 'pace_prediction' in result:
            return self._format_flow_prediction_advanced(result)
        
        # 旧形式（predict_race_flow）のフォールバック
        prediction = result.get('prediction', {})
        lines.append(f"**【ペース予想】{prediction.get('pace', '不明')}**")
        lines.append(f"確信度: {prediction.get('pace_confidence', 0)}%")
        lines.append("")
        
        # 脚質分布
        lines.append("**【脚質分布】**")
        for style_data in prediction['style_distribution']:
            horses_str = ', '.join(style_data['horses']) if style_data['horses'] else ''
            lines.append(f"• {style_data['style']}: {style_data['count']}頭")
            if horses_str:
                lines.append(f"  {horses_str}")
        lines.append("")
        
        # 詳細な逃げ馬分析
        if prediction['detailed_escapes']:
            lines.append("**【逃げ馬詳細】**")
            for escape_type, horses in prediction['detailed_escapes'].items():
                if horses:
                    lines.append(f"• {escape_type}: {', '.join(horses)}")
            lines.append("")
        
        # 有利/不利
        if prediction['advantaged_horses']:
            lines.append("**🎯 有利な馬**")
            for horse in prediction['advantaged_horses']:
                lines.append(f"• {horse}")
            lines.append("")
        
        if prediction['disadvantaged_horses']:
            lines.append("**⚠️ 不利な馬**")
            for horse in prediction['disadvantaged_horses']:
                lines.append(f"• {horse}")
            lines.append("")
        
        lines.append(f"_分析馬数: {result.get('analyzed_horses', 0)}/{result.get('total_horses', 0)}頭_")
        
        return "\n".join(lines)
    
    def _format_flow_prediction_advanced(self, result: Dict[str, Any]) -> str:
        """高度な展開予想結果をフォーマット"""
        lines = []
        lines.append("🏇 **ViewLogic展開予想**")
        
        # レース情報
        race_info = result.get('race_info', {})
        lines.append(f"{race_info.get('venue', '')} {race_info.get('race_number', '')}R")
        if race_info.get('distance'):
            lines.append(f"距離: {race_info.get('distance', '')}")
        lines.append("")
        
        # ペース予想
        pace_pred = result.get('pace_prediction', {})
        pace = pace_pred.get('pace', '不明')
        confidence = pace_pred.get('confidence', 0)
        lines.append(f"**【ペース予想】{pace}**")
        lines.append(f"確信度: {confidence}%")
        lines.append("")
        
        # 詳細な脚質分類
        detailed_styles = result.get('detailed_styles', {})
        lines.append("**【展開予想】**")
        
        for main_style, sub_styles in detailed_styles.items():
            has_horses = any(horses for horses in sub_styles.values())
            if has_horses:
                lines.append(f"\n◆ {main_style}")
                for sub_style, horses in sub_styles.items():
                    if horses:
                        horses_str = ', '.join(horses[:3])  # 最初の3頭まで表示
                        if len(horses) > 3:
                            horses_str += f" 他{len(horses)-3}頭"
                        lines.append(f"  • {sub_style}: {horses_str}")
        lines.append("")
        
        # レースシミュレーション（ゴール予想のみ）
        simulation = result.get('race_simulation', {})
        if simulation and 'finish' in simulation:
            lines.append("**【上位予想】**")
            for i, entry in enumerate(simulation['finish'][:5], 1):
                horse = entry.get('horse_name', '不明')
                lines.append(f"{i}. {horse}")
            lines.append("")
        
        # ペースに応じた狙い目
        lines.append("**【狙い目】**")
        if 'ハイペース' in pace:
            lines.append("• 後方待機の差し・追込馬が有利")
            lines.append("• 前半飛ばす逃げ・先行馬は苦戦予想")
        elif 'スローペース' in pace:
            lines.append("• 前残りの可能性大")
            lines.append("• 逃げ・先行馬を重視")
            lines.append("• 追込一辺倒は厳しい展開")
        else:
            lines.append("• 平均ペースで力勝負")
            lines.append("• 総合力の高い馬を重視")
        
        return "\n".join(lines)
    
    def _format_trend_analysis(self, result: Dict[str, Any]) -> str:
        """コース傾向分析結果をフォーマット（新しい4項目構造対応）"""
        lines = []
        lines.append("📊 **ViewLogicコース傾向分析**")
        
        course = result['course_info']
        course_key = course.get('course_key', f"{course['venue']}コース")
        lines.append(f"{course_key}")
        lines.append("")
        
        trends = result['trends']
        
        # 1. 出場馬の該当コース成績複勝率
        if trends.get('horse_course_performance'):
            lines.append("**【出場馬の当コース成績】**")
            horses = trends['horse_course_performance']
            
            # 成績がある馬のみ表示
            horses_with_data = [h for h in horses if h.get('status') == 'found' and h.get('total_runs', 0) > 0]
            horses_no_data = [h for h in horses if h.get('status') != 'found' or h.get('total_runs', 0) == 0]
            
            if horses_with_data:
                for i, horse in enumerate(horses_with_data, 1):
                    total_runs = horse.get('total_runs', 0)
                    fukusho_rate = horse.get('fukusho_rate', 0.0)
                    lines.append(f"{i}. **{horse['horse_name']}**: {total_runs}戦 複勝率{fukusho_rate:.1f}%")
                
                # 完結メッセージを追加
                lines.append("")
                lines.append(f"以上が当コースで出走経験のある{len(horses_with_data)}頭です。")
                if horses_no_data:
                    no_data_names = [h['horse_name'] for h in horses_no_data[:5]]  # 最初の5頭のみ表示
                    if len(horses_no_data) > 5:
                        lines.append(f"その他の馬（{', '.join(no_data_names)}他）は当コースでの出走経験がありません。")
                    else:
                        lines.append(f"その他の馬（{', '.join(no_data_names)}）は当コースでの出走経験がありません。")
            else:
                lines.append("出場馬全頭が当コースでの出走経験がありません。")
                lines.append("過去のデータがないため、他の要素での判断が重要になります。")
            lines.append("")
        
        # 2. 騎手の該当コース成績複勝率
        if trends.get('jockey_course_performance'):
            lines.append("**【騎手の当コース成績】**")
            jockeys = trends['jockey_course_performance']
            
            # 成績がある騎手のみ表示
            jockeys_with_data = [j for j in jockeys if j.get('status') == 'found' and j.get('total_runs', 0) > 0]
            jockeys_no_data = [j for j in jockeys if j.get('status') != 'found' or j.get('total_runs', 0) == 0]
            
            if jockeys_with_data:
                for i, jockey in enumerate(jockeys_with_data, 1):
                    total_runs = jockey.get('total_runs', 0)
                    win_rate = jockey.get('win_rate', 0.0)
                    fukusho_rate = jockey.get('fukusho_rate', 0.0)
                    # 実際のレース数を表示（7年分のデータ）
                    lines.append(f"{i}. **{jockey['jockey_name']}**: {total_runs}戦 勝率{win_rate:.1f}% 複勝率{fukusho_rate:.1f}%")
                
                # 完結メッセージを追加
                lines.append("")
                lines.append(f"以上が当コースで騎乗経験のある{len(jockeys_with_data)}名です。")
                if jockeys_no_data:
                    lines.append(f"その他の騎手は当コースでの騎乗経験がありません。")
            else:
                lines.append("出場騎手全員が当コースでの騎乗経験がありません。")
                lines.append("騎手の適性よりも馬の能力を重視した方がよいでしょう。")
            lines.append("")
        
        # 3. 騎手の枠順別複勝率
        if trends.get('jockey_post_performance'):
            lines.append("**【騎手の枠順別成績】**")
            jockey_post_data = trends['jockey_post_performance']
            
            # デバッグログ追加
            logger.info(f"🐎 騎手枠順別成績データ取得: type={type(jockey_post_data)}, keys={list(jockey_post_data.keys()) if isinstance(jockey_post_data, dict) else 'not dict'}")
            if isinstance(jockey_post_data, dict) and jockey_post_data:
                first_key = list(jockey_post_data.keys())[0]
                logger.info(f"   サンプル（{first_key}）: {jockey_post_data[first_key]}")
            
            # jockey_post_dataの型チェック
            if jockey_post_data and isinstance(jockey_post_data, dict):
                # 各騎手の個別成績を表示
                jockey_count = 0
                for jockey_name, post_stats in jockey_post_data.items():
                    # post_statsの型チェック
                    if not isinstance(post_stats, dict):
                        logger.error(f"騎手 {jockey_name} のpost_statsが辞書ではありません: type={type(post_stats)}")
                        continue
                    
                    # 今回の枠番情報を取得
                    assigned_post = post_stats.get('assigned_post')
                    post_category = post_stats.get('post_category')
                    
                    # 該当する枠番での成績を取得
                    if assigned_post and post_category:
                        # assigned_post_statsがあればそれを使用、なければall_post_statsから取得
                        assigned_stats = post_stats.get('assigned_post_stats')
                        if not assigned_stats and post_category:
                            all_stats = post_stats.get('all_post_stats', {})
                            if isinstance(all_stats, dict):
                                assigned_stats = all_stats.get(post_category, {})
                        
                        if assigned_stats and isinstance(assigned_stats, dict):
                            race_count = assigned_stats.get('race_count', 0)
                            fukusho_rate = assigned_stats.get('fukusho_rate', 0.0)
                            
                            if race_count > 0:
                                jockey_count += 1
                                # 複勝率を正常範囲（0-100%）に修正
                                if fukusho_rate > 100:
                                    # 異常に大きい値は100で割る
                                    display_rate = fukusho_rate / 100
                                elif fukusho_rate > 1.0:
                                    # 1を超える値はそのまま使用（パーセント値）
                                    display_rate = fukusho_rate
                                else:
                                    # 0.0-1.0の場合は100倍してパーセント値に
                                    display_rate = fukusho_rate * 100
                                # 100%を上限とする
                                display_rate = min(display_rate, 100.0)
                                # レース数と複勝率を表示
                                lines.append(f"{jockey_count}. **{jockey_name}**（{assigned_post}枠）: {race_count}戦 複勝率{display_rate:.1f}%")
                            else:
                                jockey_count += 1
                                lines.append(f"{jockey_count}. **{jockey_name}**（{assigned_post}枠）: データなし")
                        else:
                            jockey_count += 1
                            lines.append(f"{jockey_count}. **{jockey_name}**（{assigned_post}枠）: データなし")
                    else:
                        # 枠番情報がない場合は全体の成績を表示
                        all_stats = post_stats.get('all_post_stats', {})
                        if isinstance(all_stats, dict):
                            total_races = 0
                            total_fukusho = 0
                            for category, stats in all_stats.items():
                                if isinstance(stats, dict):
                                    races = stats.get('race_count', 0)
                                    rate = stats.get('fukusho_rate', 0.0)
                                    if races > 0:
                                        total_races += races
                                        total_fukusho += races * rate
                            
                            if total_races > 0:
                                avg_fukusho = total_fukusho / total_races
                                jockey_count += 1
                                # 全体成績でも同じ正規化を適用
                                if avg_fukusho > 100:
                                    display_avg = avg_fukusho / 100
                                elif avg_fukusho > 1.0:
                                    display_avg = avg_fukusho
                                else:
                                    display_avg = avg_fukusho * 100
                                # 100%を上限とする
                                display_avg = min(display_avg, 100.0)
                                lines.append(f"{jockey_count}. **{jockey_name}**: 複勝率{display_avg:.1f}%")
                            else:
                                jockey_count += 1
                                lines.append(f"{jockey_count}. **{jockey_name}**: データなし")
                        else:
                            jockey_count += 1
                            lines.append(f"{jockey_count}. **{jockey_name}**: データなし")
                
                # 完結メッセージを追加
                if jockey_count > 0:
                    lines.append("")
                    lines.append(f"以上が出場騎手{jockey_count}名の枠順別成績です。")
                else:
                    lines.append("出場騎手の枠順別データがありません。")
                    
            elif jockey_post_data and not isinstance(jockey_post_data, dict):
                logger.error(f"jockey_post_dataが辞書ではありません: type={type(jockey_post_data)}")
                lines.append("• 枠順別データの取得に失敗しました")
            else:
                lines.append("• 枠順別データなし")
            lines.append("")
        

        
        # インサイト
        if result.get('insights'):
            lines.append("**💡 ポイント**")
            for insight in result['insights']:
                lines.append(f"• {insight}")
        
        return "\n".join(lines)
    
    def _format_daily_trend(self, result: Dict[str, Any]) -> str:
        """当日傾向分析結果をフォーマット"""
        lines = []
        lines.append("📈 **ViewLogic当日傾向**")
        lines.append(f"{result['venue']} - {result['date']}")
        lines.append(f"実施済み: {result['races_completed']}R")
        lines.append("")
        
        trends = result['trends']
        
        # 脚質別成績
        if trends.get('running_style_performance'):
            lines.append("**【脚質別成績】**")
            for style, perf in trends['running_style_performance'].items():
                win_rate = perf.get('win_rate', 0)
                if win_rate > 1:
                    win_rate = win_rate / 100
                wins = perf.get('wins', 0)
                runs = perf.get('runs', 0)
                lines.append(f"• {style}: {wins}勝/{runs}頭 (勝率{win_rate:.0%})")
            lines.append("")
        
        # 好調騎手
        if trends.get('hot_jockeys'):
            lines.append("**【好調騎手】**")
            for jockey in trends['hot_jockeys']:
                lines.append(f"• {jockey['name']}: {jockey['wins']}勝/{jockey['runs']}騎乗")
            lines.append("")
        
        # 馬場状態
        lines.append(f"**【馬場】** {trends.get('track_condition', '良')} / {trends.get('track_bias', 'フラット')}")
        lines.append("")
        
        # 推奨事項
        if result.get('recommendations'):
            lines.append("**⭐ 推奨**")
            for rec in result['recommendations']:
                lines.append(f"• {rec}")
        
        return "\n".join(lines)
    
    def _create_imlogic_prompt(self, settings: Dict[str, Any]) -> str:
        """
        IMLogic設定からプロンプトを生成
        """
        weights = settings.get('weights', {})
        horse_ratio = settings.get('horse_ratio', 70)
        jockey_ratio = settings.get('jockey_ratio', 30)
        
        prompt_parts = [
            f"IMLogicカスタム設定による分析",
            f"馬の能力: {horse_ratio}%、騎手の能力: {jockey_ratio}%の比率で評価",
            "",
            "重視する項目（優先順位）:"
        ]
        
        # 重み付けをソートして優先順位を決定
        sorted_weights = sorted(
            weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (item, weight) in enumerate(sorted_weights, 1):
            if weight > 0:
                item_name = self._get_item_display_name(item)
                prompt_parts.append(f"{i}. {item_name} (重要度: {weight})")
        
        return "\n".join(prompt_parts)
    
    def _get_item_display_name(self, item_key: str) -> str:
        """
        項目キーから表示名を取得
        """
        display_names = {
            'distance_aptitude': '距離適性',
            'track_aptitude': 'コース適性',
            'growth_potential': '成長力',
            'trainer_skill': '調教師',
            'breakthrough_potential': '爆発力',
            'strength_score': '強さ',
            'winning_percentage': '勝率',
            'recent_performance': '近走',
            'course_experience': 'コース経験',
            'distance_experience': '距離実績',
            'stability': '安定感',
            'jockey_compatibility': '騎手相性'
        }
        return display_names.get(item_key, item_key)
    
    async def process_message(
        self,
        message: str,
        race_data: Dict[str, Any],
        ai_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        統合メッセージ処理
        
        Returns:
            {
                'content': str,  # 応答内容
                'ai_type': str,  # 使用したAI
                'sub_type': str,  # サブタイプ
                'analysis_data': dict  # 分析データ（あれば）
            }
        """
        # レースデータを保持（determine_ai_typeで使用）
        self.current_race_data = race_data
        
        # まず出走馬チェック（AI判定の前に必ず実行）
        venue = race_data.get('venue', '')
        race_number = race_data.get('race_number', '')
        race_horses = race_data.get('horses', [])

        # レースに存在しない馬名が含まれているかチェック
        # カタカナの馬名を正しく抽出（ァ-ヴーを使用）
        potential_horses = re.findall(r'[ァ-ヴー]+', message)

        for potential_horse in potential_horses:
            if len(potential_horse) >= 3:
                is_in_race = False
                for race_horse in race_horses:
                    if potential_horse in race_horse or race_horse in potential_horse:
                        is_in_race = True
                        break

                # 助詞チェックを緩和（馬名単体でも検出）
                if not is_in_race:
                    common_words = ['データ', 'レース', 'スコア', 'ポイント', 'システム', 'エラー', 'ViewLogic', 'IMLogic', 'DLogic', 'ILogic', 'FLogic', 'フェア', 'オッズ', 'ロジック', 'エフロジック', 'コラム']  # 'コラム'を除外単語に追加
                    if potential_horse not in common_words:
                        return {
                            'content': f"「{potential_horse}」は、{venue} {race_number}Rには出走しません。\nこのレースの出走馬は以下の通りです:\n" + "、".join(race_horses),
                            'ai_type': 'imlogic',  # デフォルトでimlogicを返す
                            'sub_type': 'out_of_scope',
                            'analysis_data': None
                        }
        
        # 次にレース外の質問をチェック
        if self._is_out_of_scope(message, race_data):
            # 他のレースや開催場への言及の場合
            return {
                'content': f"このチャットは{venue} {race_number}R専用です。他のレースについては新しいチャットを作成してください。",
                'ai_type': 'imlogic',  # デフォルトでimlogicを返す
                'ai_display_name': 'IMLogic AI',
                'sub_type': 'out_of_scope',
                'analysis_data': None
            }

        # コラム選択コマンドを先に処理
        if message.startswith(self.COLUMN_SELECTION_PREFIX):
            selection_id = message[len(self.COLUMN_SELECTION_PREFIX):].strip()
            content, selection_analysis = self._handle_column_selection(race_data, user_email, selection_id)
            return {
                'content': content,
                'ai_type': 'column',
                'ai_display_name': 'コラムシステム',
                'sub_type': 'selection',
                'analysis_data': selection_analysis
            }
        
        # AI タイプの決定（レース外チェックの後に移動）
        if ai_type:
            determined_ai = ai_type
            logger.info(f"AI判定(手動指定): ai_type={ai_type}, determined_ai={determined_ai}")
            # ViewLogicの場合は、メッセージからサブタイプを決定
            if ai_type == 'viewlogic':
                _, sub_type = self.determine_ai_type(message)
                # ViewLogic以外が判定された場合はデフォルトに
                if sub_type not in ['flow', 'trend', 'opinion']:
                    sub_type = 'manual'
            elif ai_type == 'flogic':
                sub_type = 'analysis'  # F-Logicは分析タイプ
            elif ai_type == 'metalogic':
                sub_type = 'analysis'  # MetaLogicは分析タイプ
            else:
                sub_type = 'manual'
        else:
            determined_ai, sub_type = self.determine_ai_type(message)
            logger.info(f"AI判定(自動): message='{message[:50]}...', determined_ai={determined_ai}, sub_type={sub_type}")

        # AI種別に応じて処理
        analysis_data = None
        if determined_ai == 'imlogic':
            result = await self.process_imlogic_message(message, race_data, settings)
            # タプルまたは辞書の場合は分解
            if isinstance(result, tuple):
                content, analysis_data = result
            elif isinstance(result, dict):
                content = result.get('content', '')
                analysis_data = result.get('analysis_data')
            else:
                content = result
        elif determined_ai == 'dlogic':
            result = await self.process_dlogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'flogic':
            result = await self.process_flogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'ilogic':
            result = await self.process_ilogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'metalogic':
            result = await self.process_metalogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'nlogic':
            result = await self.process_nlogic_message(message, race_data)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        elif determined_ai == 'column':
            logger.info(f"コラム処理開始: determined_ai={determined_ai}, user_email={user_email}")
            content, analysis_data = self._handle_column_request(race_data, user_email)
        else:  # viewlogic
            result = await self.process_viewlogic_message(message, race_data, sub_type)
            if isinstance(result, tuple):
                content, analysis_data = result
            else:
                content = result
        
        # 表示名の設定
        ai_display_names = {
            'metalogic': 'MetaLogic AI',
            'flogic': 'F-Logic AI',
            'dlogic': 'D-Logic AI',
            'ilogic': 'I-Logic AI',
            'nlogic': 'N-Logic AI',
            'imlogic': 'IMLogic AI',
            'viewlogic': 'ViewLogic AI',
            'column': 'コラムシステム'
        }
        
        # デバッグログ追加
        logger.info(f"最終レスポンス生成: determined_ai={determined_ai}, display_name={ai_display_names.get(determined_ai, 'IMLogic AI')}")

        return {
            'content': content,
            'ai_type': determined_ai,
            'ai_display_name': ai_display_names.get(determined_ai, 'IMLogic AI'),
            'sub_type': sub_type,
            'analysis_data': analysis_data
        }
    
    def _is_out_of_scope(self, message: str, race_data: Dict[str, Any]) -> bool:
        """
        メッセージがレース範囲外かチェック
        """
        # 他のレース番号への言及をチェック
        other_race_pattern = r'\d+R(?![\d])'  # 数字+R（後に数字が続かない）
        matches = re.findall(other_race_pattern, message)
        
        current_race_num = str(race_data.get('race_number', ''))
        for match in matches:
            race_num = match[:-1]  # 'R'を除去
            if race_num != current_race_num:
                return True
        
        # 他の開催場への言及をチェック
        venues = ['東京', '中山', '阪神', '京都', '中京', '小倉', '新潟', '福島', '札幌', '函館']
        current_venue = race_data.get('venue', '')
        
        for venue in venues:
            if venue in message and venue != current_venue:
                # 明確に他の開催場のレースについて聞いている場合
                if re.search(f'{venue}\\d+R', message):
                    return True
        
        # レースに存在しない馬名をチェック
        race_horses = race_data.get('horses', [])
        if race_horses:
            # メッセージから馬名らしい単語を抽出（全カタカナ文字と英字の連続）
            # ァ-ヴ で全てのカタカナ（小文字含む）とヴをカバー
            potential_horses = re.findall(r'[ァ-ヴー]+|[A-Za-z]+', message)
            
            for potential_horse in potential_horses:
                # 3文字以上で、かつレースの馬名リストに存在しない場合
                if len(potential_horse) >= 3:
                    # レースの馬名リストに存在するかチェック
                    is_in_race = False
                    for race_horse in race_horses:
                        if potential_horse in race_horse or race_horse in potential_horse:
                            is_in_race = True
                            break
                    
                    # 明らかに馬名として言及されている場合（〜の、〜は、など）
                    # ただしコラムは除外
                    if potential_horse == 'コラム':
                        continue  # コラムは馬名ではないのでスキップ

                    if not is_in_race and re.search(f'{potential_horse}(の|は|が|を|と|って|という)', message):
                        # 一般的な単語や助詞でないことを確認
                        common_words = ['データ', 'レース', 'スコア', 'ポイント', 'システム', 'エラー', 'ViewLogic', 'IMLogic', 'DLogic', 'ILogic', 'FLogic', 'フェア', 'オッズ', 'ロジック', 'エフロジック', 'コラム']
                        if potential_horse not in common_words:
                            logger.info(f"レース外の馬を検出: {potential_horse}")
                            return True
        
        return False
    
    async def process_dlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        D-Logicメッセージ処理（地方競馬対応版）
        """
        try:
            # D-Logic分析を実行する場合
            if self._should_analyze(message):
                venue = race_data.get('venue', '')
                
                # 地方競馬場の場合は地方競馬版エンジンを使用
                if self._is_local_racing(venue):
                    from services.local_fast_dlogic_engine_v2 import local_fast_dlogic_engine_v2
                    logger.info(f"🏇 地方競馬版D-Logicエンジンを使用: {venue}")

                    horses = race_data.get('horses', [])
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)

                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_dlogic',
                        race_data=race_data
                    )
                    cached_response = self._get_cached_response('dlogic_analysis', cache_key_data)
                    if cached_response:
                        return cached_response

                    posts = race_data.get('posts') or []
                    horse_numbers = race_data.get('horse_numbers') or []

                    dlogic_result: Dict[str, Dict[str, Any]] = {}
                    for idx, horse_name in enumerate(horses):
                        score_data = local_fast_dlogic_engine_v2.raw_manager.calculate_dlogic_realtime(horse_name)
                        post = posts[idx] if idx < len(posts) else None
                        horse_number = horse_numbers[idx] if idx < len(horse_numbers) else idx + 1

                        if score_data and not score_data.get('error'):
                            total_score = score_data.get('total_score', 0.0)
                            details = score_data.get('d_logic_scores') or {}
                            entry = {
                                'score': round(total_score, 1),
                                'data_available': True,
                                'details': details,
                                'horse_number': horse_number,
                                'post': post,
                                'grade': score_data.get('grade')
                            }
                        else:
                            entry = {
                                'score': None,
                                'data_available': False,
                                'horse_number': horse_number,
                                'post': post
                            }

                        dlogic_result[horse_name] = entry

                    ranked_horses = [
                        h for h in dlogic_result.keys()
                        if dlogic_result[h].get('data_available') and dlogic_result[h].get('score') is not None
                    ]
                    ranked_horses.sort(key=lambda h: dlogic_result[h]['score'], reverse=True)

                    for position, horse_name in enumerate(ranked_horses, start=1):
                        dlogic_result[horse_name]['rank'] = position

                    content = self._format_dlogic_batch_result(dlogic_result, race_data)

                    analysis_data = {
                        'type': 'dlogic',
                        'scores': dlogic_result,
                        'race_info': {
                            'venue': race_data.get('venue', ''),
                            'race_number': race_data.get('race_number', ''),
                            'race_name': race_data.get('race_name', '')
                        },
                        'top_horses': ranked_horses[:5]
                    }

                    self._save_cached_response(
                        'dlogic_analysis',
                        cache_key_data,
                        content,
                        analysis_data
                    )

                    return (content, analysis_data)
                    
                else:
                    # JRA版（既存）
                    from api.v2.dlogic import calculate_dlogic_batch
                    logger.info(f"🏇 JRA版D-Logicエンジンを使用: {venue}")
                    
                    # レース情報から馬名を抽出
                    horses = race_data.get('horses', [])
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)
                    
                    # D-Logicバッチ計算を実行
                    dlogic_result = await calculate_dlogic_batch(horses)
                    
                    if not dlogic_result:
                        return ("D-Logic分析の実行に失敗しました。", None)
                    
                    # 結果をフォーマット
                    content = self._format_dlogic_batch_result(dlogic_result, race_data)
                    
                    # 分析データを抽出
                    analysis_data = {
                        'type': 'dlogic',
                        'scores': dlogic_result,
                        'top_horses': sorted(
                            [h for h in dlogic_result.keys() if dlogic_result[h].get('data_available', False)],
                            key=lambda h: dlogic_result[h].get('score', 0),
                            reverse=True
                        )[:5]
                    }
                    
                    return (content, analysis_data)
            
            # 通常の会話の場合
            else:
                # レースコンテキストを設定
                race_context = self.create_race_context_prompt(race_data)
                
                # D-Logicの説明
                dlogic_prompt = """
D-Logicは、12項目による馬の総合評価システムです。
各馬の能力を0-100点で評価し、ランキング形式で表示します。
分析をご希望の場合は「D-Logic指数を教えて」「評価して」などとお聞きください。
"""
                
                # Claude APIを呼び出し（会話用）
                if self.anthropic_client:
                    full_prompt = f"{race_context}\n\n{dlogic_prompt}\n\nユーザーの質問: {message}"
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=2000,
                        temperature=0.7,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ]
                    )
                    return (response.content[0].text, None)
                else:
                    return ("会話機能は現在利用できません", None)
            
        except Exception as e:
            logger.error(f"D-Logic処理エラー: {e}")
            return (f"申し訳ございません。D-Logic分析中にエラーが発生しました: {str(e)}", None)
    
    async def process_flogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        F-Logicメッセージ処理（投資価値判定）
        """
        try:
            # レース情報確認
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            venue = race_data.get('venue')
            race_number = race_data.get('race_number')
            
            # F-Logicの説明要求かどうか判定
            explanation_keywords = ['って何', 'とは', '説明', 'どういう', '何ですか', '教えて']
            is_explanation = any(keyword in message for keyword in explanation_keywords)
            
            if is_explanation:
                explanation = """🎯 F-Logic（Fair Value Logic）について

F-Logicは、競馬における理論的な「フェア値（適正オッズ）」を計算し、市場オッズとの乖離から投資価値を判定するAIシステムです。

【主な機能】
• I-Logicスコアを基にした理論的勝率計算
• フェア値（理論オッズ）の算出
• 市場オッズとの乖離率分析
• 期待値とROI（投資収益率）の計算
• Kelly基準による最適投資比率提案

【投資判定の仕組み】
フェア値 < 市場オッズ → 割安（買い推奨）
フェア値 > 市場オッズ → 割高（見送り推奨）

例：フェア値5.0倍の馬が市場で10.0倍
→ オッズ乖離率2.0倍 = 強い投資価値あり

F-Logic分析をご希望の場合は「F-Logic分析して」とお聞きください。"""
                return (explanation, None)
            
            if not horses:
                return ("F-Logic分析にはレース情報が必要です。", None)
            
            # 分析要求かどうか判定
            analyze_keywords = ['分析', '計算', '判定', '価値', 'オッズ', 'フェア', '期待値']
            should_analyze = any(keyword in message for keyword in analyze_keywords)
            
            if should_analyze:
                # レースデータからオッズを取得
                odds_values = race_data.get('odds', [])
                market_odds = {}
                

                
                # オッズが存在する場合はマッピング
                if odds_values and horses:
                    for i, horse_name in enumerate(horses):
                        if i < len(odds_values):
                            odds_value = odds_values[i]
                            # オッズ値が有効な場合のみ追加
                            if odds_value and odds_value > 0:
                                market_odds[horse_name] = float(odds_value)
                    logger.info(f"F-Logic: market_odds from race_data: {list(market_odds.items())[:3]}")
                    logger.info(f"F-Logic: Total odds mapped: {len(market_odds)}")
                
                # オッズがない場合はodds_managerから取得を試みる（デバッグのため一時的に無効化）
                # if not market_odds:
                #     logger.info("F-Logic: No odds in race_data, trying odds_manager")
                #     from services.odds_manager import odds_manager
                #     market_odds = odds_manager.get_real_time_odds(
                #         venue=venue,
                #         race_number=race_number,
                #         horses=horses
                #     )
                
                # F-Logic分析実行（市場オッズが無い場合はフェア値のみ算出）
                has_market_odds = bool(market_odds)
                is_local_racing = self._is_local_racing(venue)
                if is_local_racing:
                    from services.local_flogic_engine_v2 import local_flogic_engine_v2
                    flogic_engine_instance = local_flogic_engine_v2
                    logger.info("F-Logic: 地方競馬版エンジンを使用 (%s)", venue)
                else:
                    from services.flogic_engine import flogic_engine
                    flogic_engine_instance = flogic_engine
                    logger.info("F-Logic: JRA版エンジンを使用 (%s)", venue)

                cache_key_data = None
                if is_local_racing:
                    cache_extra = {
                        'market_odds': market_odds if has_market_odds else None
                    }
                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_flogic',
                        race_data=race_data,
                        extra=cache_extra
                    )
                    cached_response = self._get_cached_response('flogic_analysis', cache_key_data)
                    if cached_response:
                        return cached_response

                result = flogic_engine_instance.analyze_race(race_data, market_odds if has_market_odds else None)
                
                if result.get('status') == 'success':
                    content = self._format_flogic_result(result, race_data)
                    if not has_market_odds:
                        content += "\n\n⚠️ 市場オッズが未提供のため、公正オッズ（フェア値）のみ表示しています。"
                    
                    # 分析データも返す
                    analysis_data = {
                        'type': 'flogic',
                        'rankings': result.get('rankings', []),
                        'has_market_odds': result.get('has_market_odds', False)
                    }
                    if cache_key_data is not None:
                        self._save_cached_response(
                            'flogic_analysis',
                            cache_key_data,
                            content,
                            analysis_data
                        )

                    return (content, analysis_data)
                else:
                    return (f"F-Logic分析エラー: {result.get('message', '不明なエラー')}", None)
            else:
                # F-Logicの説明（Claude API不要、直接返答）
                race_context = f"現在選択中: {venue}{race_number}R"
                if horses:
                    race_context += f"（{len(horses)}頭）"
                    
                explanation = f"""🎯 {race_context}

F-Logic（Fair Value Logic）は、理論的な公正オッズと市場オッズを比較して投資価値を判定するシステムです。

【主な機能】
🎯 公正価値計算: I-Logicスコアから理論的な適正オッズを算出
💰 投資価値判定: 市場オッズとの乖離から割安・割高を判定
📊 期待値計算: 投資リターンの期待値とROIを推定

【投資判断基準】
・フェア値 < 市場オッズ = 割安（買い）
・フェア値 > 市場オッズ = 割高（見送り）

分析をご希望の場合は「F-Logic分析して」「投資価値を判定」などとお聞きください。"""
                
                return (explanation, None)
                
        except Exception as e:
            logger.error(f"F-Logic処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return (f"F-Logic分析中にエラーが発生しました: {str(e)}", None)
    
    def _format_flogic_result(self, result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        F-Logic分析結果をフォーマット
        """
        try:
            rankings = result.get('rankings', [])
            if not rankings:
                return "F-Logic分析結果が取得できませんでした。"
            
            lines = []
            lines.append(f"🎯 F-Logic 投資価値分析結果")
            lines.append("=" * 40)
            
            # 全馬を投資価値順に出力
            for i, horse in enumerate(rankings, 1):
                # 順位と馬名
                lines.append(f"\n【{i}位】 {horse['horse']}")
                lines.append("-" * 30)
                
                # フェア値と市場オッズ
                lines.append(f"フェア値: {horse['fair_odds']}倍")
                if 'market_odds' in horse:
                    lines.append(f"市場オッズ: {horse['market_odds']}倍")
                    divergence = horse.get('odds_divergence', 0)
                    lines.append(f"オッズ乖離率: {divergence:.2f}倍")
                
                # 投資判断
                signal = horse.get('investment_signal', '評価なし')
                lines.append(f"投資判断: {signal}")
                
                # 期待値とROI
                if 'expected_value' in horse:
                    lines.append(f"期待値: {horse['expected_value']}")
                if 'roi_estimate' in horse:
                    lines.append(f"推定ROI: {horse['roi_estimate']}%")
                
                # I-Logicスコア
                if 'ilogic_score' in horse:
                    # I-Logicスコアは非表示（I-Logicエンジンと重複するため）
                    pass
                
                # 投資価値評価
                if horse.get('odds_divergence', 0) >= 2.0:
                    lines.append("⭐ 【非常に割安】投資価値が高い")
                elif horse.get('odds_divergence', 0) >= 1.5:
                    lines.append("✨ 【割安】良い投資機会")
                elif horse.get('odds_divergence', 0) >= 1.2:
                    lines.append("📊 【やや割安】検討価値あり")
                elif horse.get('odds_divergence', 0) >= 0.8:
                    lines.append("➖ 【適正】投資価値は普通")
                else:
                    lines.append("⚠️ 【割高】投資は見送り推奨")
            
            # 注意事項
            lines.append("\n\n※F-Logicは理論値と市場価格の乖離を分析するものです")
            lines.append("※投資は自己責任でお願いします")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"F-Logic結果フォーマットエラー: {e}")
            return "F-Logic分析結果の表示中にエラーが発生しました。"
    
    async def process_ilogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict]]:
        """
        I-Logicメッセージ処理（地方競馬対応版）
        """
        try:
            # I-Logic分析を実行する場合
            if self._should_analyze(message):
                venue = race_data.get('venue', '')
                
                # 地方競馬場の場合は地方競馬版エンジンを使用
                if self._is_local_racing(venue):
                    from services.local_race_analysis_engine_v2 import local_race_analysis_engine_v2 as local_ilogic_engine_v2
                    logger.info(f"🏇 地方競馬版I-Logicエンジンを使用: {venue}")
                    
                    # レース情報を準備
                    horses = race_data.get('horses', [])
                    jockeys = race_data.get('jockeys', [])
                    
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)
                    
                    if not jockeys:
                        return ("I-Logic分析には騎手情報が必要です。", None)
                    
                    cache_key_data = self._build_cache_key_data(
                        ai_type='nar_ilogic',
                        race_data=race_data
                    )
                    cached_response = self._get_cached_response('ilogic_analysis', cache_key_data)
                    if cached_response:
                        return cached_response

                    # 地方競馬版I-Logic計算
                    logger.info(f"地方I-Logic分析開始: horses={horses}, jockeys={jockeys}")
                    result = local_ilogic_engine_v2.analyze_race(race_data)
                    logger.info(f"地方I-Logic分析結果: status={result.get('status')}, scores数={len(result.get('scores', []))}")
                    
                    if result.get('status') == 'success':
                        scores = result.get('scores', [])
                        content = self._format_ilogic_scores_local(scores, race_data)

                        race_info = result.get('race_info') or {
                            'venue': race_data.get('venue', ''),
                            'race_number': race_data.get('race_number', ''),
                            'race_name': race_data.get('race_name', '')
                        }
                        summary = result.get('summary', {})
                        item_weights = result.get('item_weights') or {
                            '1_distance_aptitude': 8.33,
                            '2_bloodline_evaluation': 8.33,
                            '3_jockey_compatibility': 8.33,
                            '4_trainer_evaluation': 8.33,
                            '5_track_aptitude': 8.33,
                            '6_weather_aptitude': 8.33,
                            '7_popularity_factor': 8.33,
                            '8_weight_impact': 8.33,
                            '9_horse_weight_impact': 8.33,
                            '10_corner_specialist': 8.33,
                            '11_margin_analysis': 8.33,
                            '12_time_index': 8.37
                        }
                        weights = result.get('weights') or {
                            'horse': 70,
                            'jockey': 30
                        }
                        top_horses = result.get('top_horses') or [s.get('horse') for s in scores[:5] if s.get('horse')]

                        analysis_data = {
                            'type': 'ilogic',
                            'analysis_type': result.get('analysis_type', 'race_analysis_v2'),
                            'race_info': race_info,
                            'results': scores,
                            'scores': scores,
                            'summary': summary,
                            'item_weights': item_weights,
                            'weights': weights,
                            'top_horses': top_horses
                        }

                        self._save_cached_response(
                            'ilogic_analysis',
                            cache_key_data,
                            content,
                            analysis_data
                        )

                        return (content, analysis_data)
                    else:
                        return (f"I-Logic分析に失敗しました: {result.get('message', '不明なエラー')}", None)
                else:
                    # JRA版（既存の処理）
                    # レース情報を準備
                    horses = race_data.get('horses', [])
                    jockeys = race_data.get('jockeys', [])
                    posts = race_data.get('posts', [])
                    horse_numbers = race_data.get('horse_numbers', [])
                    venue = race_data.get('venue', '')
                    race_number = race_data.get('race_number', 0)
                    
                    if not horses:
                        return ("分析対象の馬が指定されていません。", None)
                    
                    # 騎手・枠順データが不足している場合
                    if not jockeys or not posts:
                        return ("I-Logic分析には騎手・枠順情報が必要です。このレースでは分析できません。", None)
                    
                    try:
                        # HTTPリクエストではなく直接関数呼び出しを使用（Render環境対応）
                        logger.info(f"I-Logic直接関数呼び出し開始: {venue} {race_number}R")
                        
                        # race-analysis-v2/chat 関数を直接呼び出し
                        from api.race_analysis_v2 import race_analysis_chat
                        
                        # APIの期待する形式に合わせる
                        request_data = {
                            'message': f"{venue} {race_number}Rを分析して",
                            'race_info': {
                                'venue': venue,
                                'race_number': race_number,
                                'horses': horses,
                                'jockeys': jockeys,
                                'posts': posts,
                                'horse_numbers': horse_numbers or list(range(1, len(horses) + 1))
                            }
                        }
                        
                        logger.info(f"I-Logic関数呼び出しデータ: {request_data}")
                        
                        # 直接関数を呼び出し
                        result_data = await race_analysis_chat(request_data)

                        logger.info(f"I-Logic関数レスポンス: {result_data}")

                        if not result_data:
                            return ("I-Logic分析から空のレスポンスを受信しました。", None)

                        if result_data.get('status') != 'success':
                            error_msg = result_data.get('response', 'I-Logic分析でエラーが発生しました')
                            return (error_msg, None)

                        response_text = result_data.get('response', '')
                        payload = result_data.get('analysis_payload')

                        if isinstance(payload, dict) and payload.get('results'):
                            structured_results = payload.get('results', [])
                            analysis_data = {
                                'type': 'ilogic',
                                'race_info': payload.get('race_info') or {
                                    'venue': venue,
                                    'race_number': race_number,
                                    'race_name': race_data.get('race_name', '')
                                },
                                'results': structured_results,
                                'summary': payload.get('summary'),
                                'weights': payload.get('weights'),
                                'item_weights': payload.get('item_weights'),
                                'top_horses': payload.get('top_horses') or [r.get('horse') for r in structured_results[:5] if r.get('horse')]
                            }

                            if not response_text:
                                response_text = self._format_imlogic_result(payload, payload.get('race_info', {}))

                            return (response_text, analysis_data)

                        if not response_text:
                            return ("I-Logic分析結果が空です。", None)

                        scores = self._parse_ilogic_response(response_text, horses)

                        analysis_data = {
                            'type': 'ilogic',
                            'response_text': response_text,
                            'top_horses': scores[:5] if scores else []
                        }

                        return (response_text, analysis_data)
                        
                    except Exception as e:
                        logger.error(f"I-Logic分析エラー: {e}")
                        import traceback
                        traceback.print_exc()
                        return ("I-Logic分析の実行中にエラーが発生しました。", None)
            
            # 通常の会話の場合
            else:
                # レースコンテキストを設定
                race_context = self.create_race_context_prompt(race_data)
                
                # I-Logicの説明
                ilogic_prompt = """
I-Logicは、馬の能力（70%）と騎手の適性（30%）を総合した分析システムです。
開催場適性、クラス補正、騎手の枠順適性などを考慮した精密な評価を行います。
分析をご希望の場合は「I-Logic分析して」「総合評価は？」などとお聞きください。
"""
                
                # Claude APIを呼び出し（会話用）
                if self.anthropic_client:
                    full_prompt = f"{race_context}\n\n{ilogic_prompt}\n\nユーザーの質問: {message}"
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=2000,
                        temperature=0.7,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ]
                    )
                    return (response.content[0].text, None)
                else:
                    return ("会話機能は現在利用できません", None)
            
        except Exception as e:
            import traceback
            logger.error(f"I-Logic処理エラー: {e}")
            logger.error(f"I-Logicスタックトレース: {traceback.format_exc()}")
            logger.error(f"I-Logicエラー時のrace_data: {race_data}")
            return (f"申し訳ございません。I-Logic分析中にエラーが発生しました: {str(e)}", None)
    
    def _parse_dlogic_result(self, content: str) -> Optional[Dict]:
        """
        D-Logic結果からスコア情報を抽出
        """
        try:
            import re
            
            # D-Logic上位5頭を抽出するパターン
            top5_pattern = r'D-Logic上位5頭[：:]\s*([^、\n]+(?:、[^、\n]+){0,4})'
            match = re.search(top5_pattern, content)
            
            if match:
                top5_horses = [horse.strip() for horse in match.group(1).split('、')]
                return {
                    'type': 'dlogic',
                    'top_horses': top5_horses
                }
            
            return None
            
        except Exception as e:
            logger.error(f"D-Logic結果パースエラー: {e}")
            return None
    
    def _format_ilogic_result(self, analysis_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        I-Logic分析結果をフォーマット
        """
        try:
            top_horses = analysis_result.get('top_horses', [])
            detailed_scores = analysis_result.get('detailed_scores', {})
            
            if not top_horses:
                return "I-Logic分析結果が取得できませんでした。"
            
            # 結果のフォーマット
            lines = []
            lines.append(f"👑 I-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R")
            lines.append("")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, horse_name in enumerate(top_horses[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                
                # 詳細スコアがあれば表示
                if horse_name in detailed_scores:
                    score_info = detailed_scores[horse_name]
                    total_score = score_info.get('total_score', 0)
                    horse_score = score_info.get('horse_score', 0)
                    jockey_score = score_info.get('jockey_score', 0)
                    
                    lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
                    lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
                else:
                    lines.append(f"{emoji} {horse_name}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"I-Logic結果フォーマットエラー: {e}")
            return "I-Logic分析結果の表示中にエラーが発生しました。"
    
    def _format_betting_recommendations(self, result: Dict[str, Any]) -> str:
        """
        ViewLogic馬券推奨結果をフォーマット（展開予想ベース）
        """
        try:
            lines = []
            lines.append("🎯 ViewLogic推奨馬券")
            
            venue = result.get('venue', '不明')
            race_number = result.get('race_number', '')
            total_horses = result.get('total_horses', 0)
            top_5_horses_with_scores = result.get('top_5_horses_with_scores', [])
            recommendations = result.get('recommendations', [])
            
            # レース情報
            if race_number:
                lines.append(f"{venue} {race_number}R")
            else:
                lines.append(f"{venue}")
            lines.append("")
            
            # 上位5頭をカード形式で表示
            if top_5_horses_with_scores:
                lines.append("【上位5頭】")
                emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
                for i, horse_info in enumerate(top_5_horses_with_scores[:5]):
                    emoji = emojis[i] if i < 5 else f"{i+1}位:"
                    horse_name = horse_info.get('horse_name', '不明')
                    score = horse_info.get('score', 0)
                    # スコアが0の場合は点数を表示しない
                    if score > 0:
                        lines.append(f"{emoji} {i+1}位: {horse_name} ({score:.1f}点)")
                    else:
                        lines.append(f"{emoji} {i+1}位: {horse_name}")
            
            lines.append("")
            
            if not recommendations:
                lines.append("⚠️ 推奨馬券を生成できませんでした。")
                return "\n".join(lines)
            
            lines.append("【推奨馬券】")
            lines.append("")
            
            for rec in recommendations:
                rec_type = rec.get('type', '不明')
                ticket_type = rec.get('ticket_type', '馬券')
                horses = rec.get('horses', [])
                confidence = rec.get('confidence', 0)
                reason = rec.get('reason', '')
                buy_type = rec.get('buy_type', '')
                combinations = rec.get('combinations', 0)
                
                # 推奨馬券のアイコン
                icon_map = {
                    '単勝': '🥇',
                    '馬連BOX': '📦',
                    '3連単流し': '🎯',
                    'ワイド': '🌟',
                    '3連複BOX': '💰'
                }
                icon = icon_map.get(rec_type, '🎪')
                
                lines.append(f"{icon} **{rec_type}**")
                
                # 馬名の表示（複雑な形式に対応）
                if isinstance(horses, dict):
                    # 流し買いの場合（3連単など）
                    if '1着' in horses:
                        lines.append(f"  【{ticket_type}】")
                        lines.append(f"   1着: {', '.join(horses['1着'])}")
                        lines.append(f"   2着: {', '.join(horses['2着'])}")  
                        lines.append(f"   3着: {', '.join(horses['3着'])}")
                    elif '軸' in horses:
                        # ワイドの場合
                        lines.append(f"  【{ticket_type}】 {horses['軸']} 軸")
                        lines.append(f"   相手: {', '.join(horses['相手'])}")
                elif isinstance(horses, list):
                    # 通常のBOX買いまたは単勝
                    if buy_type == 'BOX':
                        lines.append(f"  【{ticket_type}BOX】 {' - '.join(horses)}")
                    else:
                        lines.append(f"  【{ticket_type}】 {' → '.join(horses)}")
                
                # 買い方詳細
                if buy_type and combinations > 0:
                    lines.append(f"   買い方: {buy_type} ({combinations}点買い)")
                lines.append(f"   📊 信頼度: {confidence}%")
                if reason:
                    lines.append(f"   💭 {reason}")
            
            lines.append("")
            lines.append("※ ViewLogic展開予想の上位馬を基にした推奨馬券です")
            lines.append("※ 投資は自己責任でお願いします")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"馬券推奨フォーマットエラー: {e}")
            import traceback
            traceback.print_exc()
            return "馬券推奨結果の表示中にエラーが発生しました。"
    
    def _format_dlogic_batch_result(self, dlogic_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        D-Logicバッチ計算結果をフォーマット
        """
        try:
            if not dlogic_result:
                return "D-Logic分析結果が取得できませんでした。"
            
            # スコアがある馬を抽出してソート
            valid_horses = []
            for horse_name, data in dlogic_result.items():
                if data.get('data_available', False) and data.get('score') is not None:
                    valid_horses.append((horse_name, data))
            
            # スコア順にソート
            valid_horses.sort(key=lambda x: x[1].get('score', 0), reverse=True)
            
            # 結果のフォーマット
            lines = []
            lines.append(f"🎯 D-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R {race_data.get('race_name', '')}")
            lines.append("")
            
            # 全頭を順位付きで表示（I-Logic形式）
            emojis = ['🥇', '🥈', '🥉']
            for i, (horse_name, data) in enumerate(valid_horses):
                # 上位3位まで絵文字、4位以降は数字表示
                if i < 3:
                    rank_display = f"{emojis[i]} {i+1}位:"
                else:
                    rank_display = f"{i+1}位:"
                
                score = data.get('score', 0)
                lines.append(f"{rank_display} {horse_name}: {score:.1f}点")
                
                # 詳細スコアがあれば表示（上位5頭のみ）
                if i < 5 and data.get('details'):
                    details = data['details']
                    # 主要な項目を表示
                    if 'distance_aptitude' in details:
                        lines.append(f"   距離適性: {details['distance_aptitude']:.1f}")
                    if 'bloodline_evaluation' in details:
                        lines.append(f"   血統評価: {details['bloodline_evaluation']:.1f}")
                
                # 次の馬との間に空行を追加（最後の馬以外）
                if i < len(valid_horses) - 1:
                    lines.append("")
                
                # 6位目に区切り線を追加
                if i == 5:
                    lines.append("【6位以下】")
            
            # データがない馬がいる場合の注記
            no_data_horses = [name for name, data in dlogic_result.items() 
                            if not data.get('data_available', False)]
            if no_data_horses:
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータベースにデータがありません:")
                lines.append(f"{', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"D-Logic結果フォーマットエラー: {e}")
            return "D-Logic分析結果の表示中にエラーが発生しました。"
    
    def _parse_ilogic_response(self, response_text: str, horses: List[str]) -> List[str]:
        """
        I-Logicレスポンステキストから馬名順位を抽出
        """
        try:
            import re
            
            # テキストから馬名を順位順に抽出
            extracted_horses = []
            
            # 各馬名が何位に表示されているかチェック
            for horse in horses:
                for line in response_text.split('\n'):
                    if horse in line and ('位' in line or '🥇' in line or '🥈' in line or '🥉' in line or '🏅' in line):
                        if horse not in extracted_horses:
                            extracted_horses.append(horse)
                            break
            
            return extracted_horses
            
        except Exception as e:
            logger.error(f"I-Logicレスポンス解析エラー: {e}")
            return []
    
    def _format_ilogic_api_result(self, scores: List[Dict[str, Any]], race_data: Dict[str, Any]) -> str:
        """
        I-Logic API結果をフォーマット（V1互換）
        """
        try:
            if not scores:
                return "I-Logic分析結果が取得できませんでした。"
            
            # 結果のフォーマット
            lines = []
            lines.append(f"👑 I-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R {race_data.get('race_name', '')}")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, score_data in enumerate(scores[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                horse_name = score_data.get('horse', '不明')
                total_score = score_data.get('score', 0)
                
                lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
            
            # 6位以下も簡潔に表示
            if len(scores) > 5:
                lines.append("")
                lines.append("【6位以下】")
                for score_data in scores[5:]:
                    horse_name = score_data.get('horse', '不明')
                    total_score = score_data.get('score', 0)
                    lines.append(f"{horse_name}: {total_score:.1f}点")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"I-Logic API結果フォーマットエラー: {e}")
            return "I-Logic分析結果の表示中にエラーが発生しました。"
    
    def _format_ilogic_scores_local(self, scores: List[Dict[str, Any]], race_data: Dict[str, Any]) -> str:
        """地方競馬版I-Logicスコアのフォーマット"""
        venue = race_data.get('venue', '不明')
        race_number = race_data.get('race_number', '不明')
        
        content = f"🎯 I-Logic分析結果\n"
        content += f"{venue} {race_number}R\n\n"
        
        if not scores:
            return content + "分析データがありません。"
        
        # スコア順にソート
        scores.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # 上位5頭を表示
        for i, score in enumerate(scores[:5], 1):
            horse = score.get('horse', '不明')
            jockey = score.get('jockey', '不明')
            total = score.get('total_score', 0)
            horse_score = score.get('horse_score', 0)
            jockey_score = score.get('jockey_score', 0)
            
            if i == 1:
                content += f"🥇 {i}位: {horse}: {total:.1f}点\n"
            elif i == 2:
                content += f"🥈 {i}位: {horse}: {total:.1f}点\n"
            elif i == 3:
                content += f"🥉 {i}位: {horse}: {total:.1f}点\n"
            else:
                content += f"{i}位: {horse}: {total:.1f}点\n"
            
            content += f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点\n\n"
        
        # 6位以下
        if len(scores) > 5:
            content += "【6位以下】\n"
            for i, score in enumerate(scores[5:], 6):
                horse = score.get('horse', '不明')
                total = score.get('total_score', 0)
                horse_score = score.get('horse_score', 0)
                jockey_score = score.get('jockey_score', 0)
                
                content += f"{i}位: {horse}: {total:.1f}点\n"
                content += f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点\n"
                
                # 次の馬との間に空行を追加（最後の馬以外）
                if i < len(scores) - 1:
                    content += "\n"
        
        return content
    
    def _format_ilogic_batch_result(self, ilogic_result: Dict[str, Any], race_data: Dict[str, Any]) -> str:
        """
        I-Logicバッチ計算結果をフォーマット
        """
        try:
            if not ilogic_result:
                return "I-Logic分析結果が取得できませんでした。"
            
            # スコアがある馬を抽出してソート
            valid_horses = []
            for horse_name, data in ilogic_result.items():
                if data.get('data_available', False) and data.get('score') is not None:
                    valid_horses.append((horse_name, data))
            
            # スコア順にソート
            valid_horses.sort(key=lambda x: x[1].get('score', 0), reverse=True)
            
            # 結果のフォーマット
            lines = []
            lines.append(f"👑 I-Logic分析結果")
            lines.append(f"{race_data.get('venue', '')} {race_data.get('race_number', '')}R {race_data.get('race_name', '')}")
            
            # 上位5頭を表示
            emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
            for i, (horse_name, data) in enumerate(valid_horses[:5]):
                emoji = emojis[i] if i < 5 else f"{i+1}."
                total_score = data.get('score', 0)
                horse_score = data.get('horse_score', 0)
                jockey_score = data.get('jockey_score', 0)
                
                lines.append(f"{emoji} {horse_name}: {total_score:.1f}点")
                lines.append(f"   馬: {horse_score:.1f}点 | 騎手: {jockey_score:.1f}点")
            
            # 6位以下も簡潔に表示
            if len(valid_horses) > 5:
                lines.append("")
                lines.append("【6位以下】")
                for horse_name, data in valid_horses[5:]:
                    total_score = data.get('score', 0)
                    lines.append(f"{horse_name}: {total_score:.1f}点")
            
            # データがない馬がいる場合の注記
            no_data_horses = [name for name, data in ilogic_result.items() 
                            if not data.get('data_available', False)]
            if no_data_horses:
                lines.append("")
                lines.append("【データ不足】")
                lines.append(f"以下の馬はデータ不足のため分析できませんでした:")
                lines.append(f"{', '.join(no_data_horses)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"I-Logic結果フォーマットエラー: {e}")
            return "I-Logic分析結果の表示中にエラーが発生しました。"
    
    def _format_betting_recommendations(self, result: Dict[str, Any]) -> str:
        """
        ViewLogic馬券推奨結果をフォーマット（展開予想ベース）
        """
        try:
            lines = []
            lines.append("🎯 ViewLogic推奨馬券")
            
            venue = result.get('venue', '不明')
            race_number = result.get('race_number', '')
            total_horses = result.get('total_horses', 0)
            top_5_horses_with_scores = result.get('top_5_horses_with_scores', [])
            recommendations = result.get('recommendations', [])
            
            # レース情報
            if race_number:
                lines.append(f"{venue} {race_number}R")
            else:
                lines.append(f"{venue}")
            lines.append("")
            
            # 上位5頭をカード形式で表示
            if top_5_horses_with_scores:
                lines.append("【上位5頭】")
                emojis = ['🥇', '🥈', '🥉', '4位:', '5位:']
                for i, horse_info in enumerate(top_5_horses_with_scores[:5]):
                    emoji = emojis[i] if i < 5 else f"{i+1}位:"
                    horse_name = horse_info.get('horse_name', '不明')
                    score = horse_info.get('score', 0)
                    # スコアが0の場合は点数を表示しない
                    if score > 0:
                        lines.append(f"{emoji} {i+1}位: {horse_name} ({score:.1f}点)")
                    else:
                        lines.append(f"{emoji} {i+1}位: {horse_name}")
            
            lines.append("")
            
            if not recommendations:
                lines.append("⚠️ 推奨馬券を生成できませんでした。")
                return "\n".join(lines)
            
            lines.append("【推奨馬券】")
            lines.append("")
            
            for rec in recommendations:
                rec_type = rec.get('type', '不明')
                ticket_type = rec.get('ticket_type', '馬券')
                horses = rec.get('horses', [])
                confidence = rec.get('confidence', 0)
                reason = rec.get('reason', '')
                buy_type = rec.get('buy_type', '')
                combinations = rec.get('combinations', 0)
                
                # 推奨馬券のアイコン
                icon_map = {
                    '単勝': '🥇',
                    '馬連BOX': '📦',
                    '3連単流し': '🎯',
                    'ワイド': '🌟',
                    '3連複BOX': '💰'
                }
                icon = icon_map.get(rec_type, '🎪')
                
                lines.append(f"{icon} **{rec_type}**")
                
                # 馬名の表示（複雑な形式に対応）
                if isinstance(horses, dict):
                    # 流し買いの場合（3連単など）
                    if '1着' in horses:
                        lines.append(f"  【{ticket_type}】")
                        lines.append(f"   1着: {', '.join(horses['1着'])}")
                        lines.append(f"   2着: {', '.join(horses['2着'])}")  
                        lines.append(f"   3着: {', '.join(horses['3着'])}")
                    elif '軸' in horses:
                        # ワイドの場合
                        lines.append(f"  【{ticket_type}】 {horses['軸']} 軸")
                        lines.append(f"   相手: {', '.join(horses['相手'])}")
                elif isinstance(horses, list):
                    # 通常のBOX買いまたは単勝
                    if buy_type == 'BOX':
                        lines.append(f"  【{ticket_type}BOX】 {' - '.join(horses)}")
                    else:
                        lines.append(f"  【{ticket_type}】 {' → '.join(horses)}")
                
                # 買い方詳細
                if buy_type and combinations > 0:
                    lines.append(f"   買い方: {buy_type} ({combinations}点買い)")
                lines.append(f"   📊 信頼度: {confidence}%")
                if reason:
                    lines.append(f"   💭 {reason}")
            
            lines.append("")
            lines.append("※ ViewLogic展開予想の上位馬を基にした推奨馬券です")
            lines.append("※ 投資は自己責任でお願いします")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"馬券推奨フォーマットエラー: {e}")
            import traceback
            traceback.print_exc()
            return "馬券推奨結果の表示中にエラーが発生しました。"
    
    def _format_horse_history(self, result: Dict[str, Any], horse_name: str) -> str:
        """馬の過去データをモバイル最適化フォーマットで表示"""
        lines = []
        lines.append(f"🏇 **{horse_name} 過去戦績**")
        lines.append("")
        
        if result["status"] == "success" and result["races"]:
            races = result["races"]
            lines.append(f"📊 **直近{len(races)}戦のデータ**")
            lines.append("")
            
            for i, race in enumerate(races, 1):
                # レース基本情報（新しい絵文字付きキーと旧キーの両方に対応）
                race_date = race.get("📅 開催日", race.get("開催日", "不明"))
                venue = race.get("🏟️ 競馬場", race.get("競馬場", "不明"))
                race_name = race.get("🏁 レース", race.get("レース", ""))
                class_name = race.get("🏆 クラス", race.get("クラス", ""))
                distance = race.get("📏 距離", race.get("距離", "不明"))
                track = race.get("🌤️ 馬場", race.get("馬場", ""))
                # 血統情報の取得（ViewLogic血統分析サブエンジンがあるため、ここでは使用しない）
                # sire = race.get("🐴 父", race.get("父", ""))
                # broodmare_sire = race.get("🐎 母父", race.get("母父", ""))
                
                # 日付フォーマットの改善（例: 2025/0608 → 2025/06/08）
                if race_date != "不明" and len(race_date) == 9 and "/" in race_date:
                    parts = race_date.split("/")
                    if len(parts) == 2 and len(parts[1]) == 4:
                        year = parts[0]
                        month = parts[1][:2]
                        day = parts[1][2:]
                        race_date = f"{year}/{month}/{day}"
                
                # レース名とクラス名の表示（どちらか一方でも表示）
                if race_name or class_name:
                    # レース名とクラス名の組み合わせを適切に処理
                    if race_name and class_name and class_name not in race_name:
                        race_display = f"{race_name}（{class_name}）"
                    elif race_name:
                        race_display = race_name
                    else:  # class_nameのみの場合
                        race_display = class_name
                    lines.append(f"**{i}. {race_date} {venue} {race_display}**")
                else:
                    # レース名もクラス名もない場合はレース番号のみ
                    race_num = race.get("🏁 レース", race.get("レース", ""))
                    if race_num:
                        lines.append(f"**{i}. {race_date} {venue} {race_num}**")
                    else:
                        lines.append(f"**{i}. {race_date} {venue}**")
                
                # 距離と馬場（馬場が空の場合は「-」を表示）
                track_display = track if track else "-"
                lines.append(f"　📏 距離: {distance} / 馬場: {track_display}")
                
                # 成績情報（新しい絵文字付きキーと旧キーの両方に対応）
                chakujun = race.get("🥇 着順", race.get("着順", ""))
                # "11着" のような形式から数字部分を抽出
                if chakujun and "着" in str(chakujun):
                    chakujun = str(chakujun).replace("着", "")
                # 先頭の0を削除（"02" → "2"）
                if chakujun and str(chakujun).startswith("0") and len(str(chakujun)) > 1:
                    chakujun = str(chakujun).lstrip("0")
                
                if chakujun and str(chakujun) != "":
                    # 1-3着は強調表示
                    if str(chakujun) in ["1", "2", "3"]:
                        chakujun_display = f"**🏆 {chakujun}着**"
                    else:
                        chakujun_display = f"{chakujun}着"
                else:
                    chakujun_display = "-"
                
                popularity = race.get("📊 人気", race.get("人気", ""))
                # "10番人気" のような形式から数字部分を抽出
                if popularity and "番人気" in str(popularity):
                    popularity = str(popularity).replace("番人気", "")
                if popularity and str(popularity) != "":
                    popularity_display = f"{popularity}番人気"
                else:
                    popularity_display = "-"
                
                lines.append(f"　📊 着順: {chakujun_display} / 人気: {popularity_display}")
                
                # タイムと上り（新しい絵文字付きキーと旧キーの両方に対応）
                time_result = race.get("⏱️ タイム", race.get("タイム", ""))
                agari = race.get("🏃 上り", race.get("上り", ""))
                
                # タイムの表示改善（例: 1588 → 1:58.8）
                time_display = "-"
                if time_result and str(time_result).isdigit():
                    time_str = str(time_result)
                    if len(time_str) == 4:  # 1588のような形式
                        time_display = f"{time_str[0]}:{time_str[1:3]}.{time_str[3]}"
                    elif len(time_str) == 3:  # 589のような形式（1分未満）
                        time_display = f"0:{time_str[0:2]}.{time_str[2]}"
                    else:
                        time_display = time_result
                elif time_result:
                    time_display = time_result
                
                # 上りの表示改善（例: 334 → 33.4）
                agari_display = "-"
                if agari and str(agari) != "":
                    agari_str = str(agari).replace("秒", "")  # "334秒"から"秒"を削除
                    try:
                        if agari_str.isdigit():
                            agari_int = int(agari_str)
                            if agari_int > 100:  # 334のような形式の場合
                                agari_display = f"{agari_int/10:.1f}秒"
                            else:
                                agari_display = f"{agari_int:.1f}秒"
                        else:
                            agari_float = float(agari_str)
                            if agari_float > 100:  # 343.0のような形式の場合
                                agari_display = f"{agari_float/10:.1f}秒"
                            else:
                                agari_display = f"{agari_float:.1f}秒"
                    except:
                        agari_display = str(agari) if agari else "-"
                
                lines.append(f"　⏱ タイム: {time_display} / 上り: {agari_display}")

                # 血統情報を表示（ViewLogic血統分析サブエンジンがあるため、ここでは表示しない）
                # if sire or broodmare_sire:
                #     bloodline_parts = []
                #     if sire and sire != "不明":
                #         bloodline_parts.append(f"父: {sire}")
                #     if broodmare_sire and broodmare_sire != "不明":
                #         bloodline_parts.append(f"母父: {broodmare_sire}")
                #     if bloodline_parts:
                #         lines.append(f"　🧬 血統: {' / '.join(bloodline_parts)}")
                
                # レース名があれば追加（注：これは別のレース名フィールド）
                extra_race_name = race.get("レース名", "")
                if extra_race_name and extra_race_name != race_name:  # 重複を避ける
                    lines.append(f"　📋 {extra_race_name}")
                
                # 騎手名があれば追加  
                jockey = race.get("🏇 騎手", race.get("騎手", ""))
                if jockey:
                    lines.append(f"　🏇 騎手: {jockey}")
                
                lines.append("")
            
            # 統計情報
            # 2024-09-11: 地方競馬版の勝率・複勝率計算にバグがあるため一時的にコメントアウト
            # TODO: 計算ロジック修正後に復活させる
            """
            total_races = result.get("total_races", len(races))
            if total_races > 0:
                lines.append("📈 **戦績サマリー**")
                lines.append(f"　総戦数: {total_races}戦")
                
                # 着順分析（整数型と文字列型、絵文字付きキーの両方に対応）
                win_count = 0
                place_count = 0
                valid_races = []
                
                for r in races:
                    # 着順データを取得（新旧両方のキーに対応）
                    chakujun = r.get("🥇 着順", r.get("着順", ""))
                    # "11着" のような形式から数字部分を抽出
                    if chakujun and "着" in str(chakujun):
                        chakujun = str(chakujun).replace("着", "")
                    
                    # 有効な着順データかチェック
                    if chakujun and str(chakujun).isdigit():
                        valid_races.append({"着順": int(chakujun)})
                        if str(chakujun) == "1":
                            win_count += 1
                        if str(chakujun) in ["1", "2", "3"]:
                            place_count += 1
                if valid_races:
                    win_rate = (win_count / len(valid_races)) * 100
                    place_rate = (place_count / len(valid_races)) * 100
                    lines.append(f"　🥇 勝率: {win_rate:.1f}% ({win_count}/{len(valid_races)})")
                    lines.append(f"　🏅 複勝率: {place_rate:.1f}% ({place_count}/{len(valid_races)})")
                    
                    # 平均着順
                    avg_position = sum(int(r.get("着順")) for r in valid_races) / len(valid_races)
                    lines.append(f"　📊 平均着順: {avg_position:.1f}着")
                else:
                    lines.append("　※ 着順データが不足しています")
            """
        
        else:
            lines.append("❌ **データが見つかりません**")
            lines.append(f"　{horse_name}の過去戦績データが存在しないか、")
            lines.append("　データベースから取得できませんでした。")
        
        return "\n".join(lines)
    
    def _format_jockey_history(self, result: Dict[str, Any], jockey_name: str) -> str:
        """騎手の過去データをモバイル最適化フォーマットで表示"""
        lines = []
        lines.append(f"👤 **{jockey_name}騎手 データ**")
        lines.append("")
        
        if result["status"] == "success" and result.get("statistics"):
            stats = result["statistics"]
            
            # 総合成績を表示
            lines.append("📈 **総合成績（直近データ）**")
            total_races = stats.get('total_races', 0)
            place_rate = stats.get('place_rate', 0)
            
            if total_races > 0:
                lines.append(f"　分析対象: {total_races}戦")
                lines.append(f"　複勝率: {place_rate:.1f}%")
            else:
                lines.append("　分析対象: 0戦")
            lines.append("")
            
            # 場所別成績（地方競馬版の特徴）
            if stats.get('top_venues'):
                lines.append("🏟️ **主な競馬場別成績**")
                for venue_stat in stats['top_venues']:
                    lines.append(f"　{venue_stat}")
                lines.append("")
            
            # recent_ridesからデータ表示（出走数が0でない場合のみ表示）
            if result.get("recent_rides"):
                lines.append("🏟️ **競馬場・距離別成績（直近データ）**")
                displayed_any = False
                
                for ride in result["recent_rides"]:
                    venue = ride.get("競馬場", "不明")
                    distance = ride.get("距離", "不明")
                    runs = ride.get("出走数", 0)
                    fukusho_rate = ride.get("複勝率", "0.0%")
                    
                    # 出走数が0でない場合のみ表示
                    if runs > 0:
                        # 騎手ナレッジファイルは直近5戦のみ保持
                        display_runs = f"直近{runs}戦" if runs <= 5 else f"{runs}戦"
                        lines.append(f"　{venue}{distance}: {display_runs} 複勝率{fukusho_rate}")
                        displayed_any = True
                
                if not displayed_any:
                    lines.append("　データなし")
                lines.append("")
            
            # 統計情報から馬場状態別成績
            if stats.get("馬場別成績"):
                lines.append("🌧️ **馬場状態別成績（直近データ）**")
                track_stats = stats["馬場別成績"]
                
                # 重複を除去して表示
                seen_conditions = set()
                for track_data in track_stats:
                    condition = track_data.get("馬場", "不明")
                    rate = track_data.get("複勝率", "0.0%")
                    
                    # 「平地・芝」など同じ条件は1回だけ表示
                    if condition not in seen_conditions:
                        lines.append(f"　{condition}: 複勝率{rate}")
                        seen_conditions.add(condition)
                
                lines.append("")
            
            # 枠順別成績
            if stats.get("枠順別成績"):
                lines.append("🎯 **枠順別成績（直近データ）**")
                post_stats = stats["枠順別成績"]
                
                for post_data in post_stats:
                    post = post_data.get("枠", "不明")
                    rate = post_data.get("複勝率", "0.0%")
                    lines.append(f"　{post}: 複勝率{rate}")
                
                lines.append("")
            
            # 総合統計は既に上部で表示済みのため、ここでは表示しない

        
        else:
            lines.append("❌ **データが見つかりません**")
            lines.append(f"　{jockey_name}騎手のデータが存在しないか、")
            lines.append("　データベースから取得できませんでした。")
        
        return "\n".join(lines)
    
    def _get_viewlogic_5race_guide(self, race_data: Dict[str, Any]) -> str:
        """ViewLogic５走の使い方案内メッセージ"""
        venue = race_data.get('venue', '')
        race_number = race_data.get('race_number', '')
        
        lines = []
        lines.append("🏇 **ViewLogic５走の使い方**")
        lines.append("")
        lines.append(f"**{venue}{race_number}R**に出走する**馬名**または**騎手名**を1つだけ入力してください。")
        lines.append("")
        lines.append("📊 **出力データ**")
        lines.append("• ナレッジデータベースから**直近5走**の詳細データを表示")
        lines.append("• レース結果、着順、タイム、条件等の履歴情報")
        lines.append("• 成績分析（勝率、複勝率、平均着順）")
        lines.append("")
        lines.append("💡 **入力例**")
        lines.append("• 馬名のみ：「ドウデュース」")
        lines.append("• 騎手名のみ：「武豊」")
        lines.append("• フルネーム：「北村友一の過去5走」")
        lines.append("")
        lines.append("⚠️ **注意事項**")
        lines.append("• **1回の入力で1つの対象のみ**分析可能")
        lines.append("• 複数の馬名や騎手名を同時に入力すると反応しません")
        lines.append("• このレースに出走しない馬・騎手は分析できません")
        lines.append("")
        lines.append("🔄 **データ更新**")
        lines.append("• ナレッジデータベースは**毎月第一月曜日**に更新")
        lines.append("• 最新の競走結果が反映されています")
        lines.append("")
        lines.append("✨ さっそく馬名または騎手名を1つ入力して試してみてください！")

        return "\n".join(lines)

    def _generate_sire_analysis(self, race_data: Dict[str, Any], mode: str = 'both') -> Tuple[str, Optional[Dict]]:
        """
        種牡馬分析を生成
        出走馬の父、母、母父を表示 + 産駒成績を追加

        Args:
            race_data: レースデータ
            mode: 'both'（父と母父）、'father'（父のみ）、'broodmare'（母父のみ）

        Returns:
            (content, analysis_data) のタプル
        """
        try:
            import unicodedata

            venue = race_data.get('venue', '')
            race_number = race_data.get('race_number', '')
            horses = race_data.get('horses', [])
            distance_value = race_data.get('distance', '')

            normalized_distance_value = distance_value
            if isinstance(distance_value, str):
                normalized_distance_value = unicodedata.normalize('NFKC', distance_value).strip()

            raw_track_type = (
                race_data.get('track_type')
                or race_data.get('track')
                or race_data.get('surface')
                or race_data.get('course_type')
            )
            track_type = self._normalize_track_type(raw_track_type)
            
            if not track_type and isinstance(normalized_distance_value, str):
                if '芝' in normalized_distance_value:
                    track_type = '芝'
                elif 'ダート' in normalized_distance_value or '砂' in normalized_distance_value:
                    track_type = 'ダート'
                elif '障害' in normalized_distance_value:
                    track_type = '障害'

            distance = ''
            if isinstance(distance_value, (int, float)) and not isinstance(distance_value, bool):
                distance = str(int(distance_value))
            elif isinstance(normalized_distance_value, str):
                digit_chars = ''.join(ch for ch in normalized_distance_value if ch.isdigit())
                distance = digit_chars
            elif distance_value:
                distance = str(distance_value)

            if isinstance(distance, str):
                distance = distance.strip()
                if distance.endswith(('m', 'M')):
                    distance = distance[:-1].strip()
                if distance and not distance.isdigit():
                    digit_chars = ''.join(ch for ch in distance if ch.isdigit())
                    distance = digit_chars

            course_suffix = ''
            if distance:
                course_suffix = f"{distance}m"
            elif isinstance(normalized_distance_value, str) and normalized_distance_value:
                course_suffix = normalized_distance_value

            course_label = f"{venue}{course_suffix}" if course_suffix else venue

            # 地方競馬かどうかを判定
            is_local = self._is_local_racing(venue)

            # 統合ナレッジファイルからデータを取得
            # is_localに応じて適切なマネージャーを選択
            dlogic_manager = self.local_dlogic_manager if is_local else self.dlogic_manager

            lines = []
            # modeに応じてタイトルを変更
            if mode == 'father':
                lines.append("**血統分析（父のみ）**")
            elif mode == 'broodmare':
                lines.append("**血統分析（母父のみ）**")
            else:
                lines.append("**血統分析**")
            lines.append(f"【{venue} {race_number}R】")
            lines.append("")

            # SirePerformanceAnalyzerから産駒成績を取得する準備
            venue_code = None
            if distance:
                if is_local:
                    # 地方競馬の会場コードマッピング
                    local_venue_codes = {
                        '大井': '42',
                        '川崎': '43',
                        '船橋': '44',
                        '浦和': '45',
                        '盛岡': '35',
                        '水沢': '36'
                    }
                    venue_code = local_venue_codes.get(venue, '')
                else:
                    # JRAの会場コードマッピング
                    venue_codes = {
                        '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
                        '東京': '05', '中山': '06', '中京': '07', '京都': '08',
                        '阪神': '09', '小倉': '10'
                    }
                    venue_code = venue_codes.get(venue, '')
                
                # 距離を文字列に変換（例: 2400m → '2400'）
                if isinstance(distance, str) and distance.endswith('m'):
                    distance = distance[:-1]
                distance = str(distance)

            def serialize_performance(perf: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
                if not perf or perf.get('message'):
                    return None
                return {
                    'total_races': perf.get('total_races'),
                    'wins': perf.get('wins'),
                    'win_rate': perf.get('win_rate'),
                    'place_rate': perf.get('place_rate'),
                    'by_condition': perf.get('by_condition', [])
                }

            entries: List[Dict[str, Any]] = []

            # 各馬の血統データを取得
            for i, horse in enumerate(horses):
                horse_number = i + 1

                # 馬名を取得（辞書形式と文字列形式の両方に対応）
                if isinstance(horse, dict):
                    horse_name = horse.get('馬名', horse.get('name', ''))
                else:
                    horse_name = str(horse)

                if not horse_name:
                    continue

                # 血統データを取得
                pedigree_data = self._get_horse_pedigree(dlogic_manager, horse_name)

                entry: Dict[str, Any] = {
                    'horse_number': horse_number,
                    'horse_name': horse_name,
                }

                # 馬番をシンプルな数字表記に

                # フォーマット出力
                lines.append(f"【{horse_number}番】 **{horse_name}**")

                if pedigree_data:
                    sire = pedigree_data.get('sire', 'データなし')
                    dam = pedigree_data.get('dam', None)
                    broodmare_sire = pedigree_data.get('broodmare_sire', 'データなし')

                    entry['sire'] = sire
                    if dam:
                        entry['dam'] = dam
                    entry['broodmare_sire'] = broodmare_sire

                    # modeに応じて表示内容を変更
                    if mode == 'father':
                        # 父のみ表示
                        lines.append(f"  ◆ 父　：{sire}")
                    elif mode == 'broodmare':
                        # 母父のみ表示
                        lines.append(f"  ◆ 母父：{broodmare_sire}")
                    else:
                        # 両方表示（デフォルト）
                        lines.append(f"  ◆ 父　：{sire}")
                        if dam and dam != '':
                            lines.append(f"  ◆ 母　：{dam}")
                        lines.append(f"  ◆ 母父：{broodmare_sire}")

                    # 血統情報と産駒成績を見やすく分離
                    lines.append("")

                    # 産駒成績を追加（SirePerformanceAnalyzerを使用）
                    # is_localに応じて適切なAnalyzerを選択
                    analyzer = self.local_sire_analyzer if is_local else self.sire_analyzer
                    if analyzer:
                        try:
                            # modeに応じて産駒成績を取得・表示
                            if mode != 'broodmare':
                                # 父の産駒成績を取得（father または both の場合）
                                if sire and sire != 'データなし':
                                    sire_perf = analyzer.analyze_sire_performance(
                                        sire, venue_code, distance, track_type
                                    )
                                    if 'message' not in sire_perf:
                                        father_label = course_label if distance else f"{course_label}"
                                        lines.append(f"    └ 父 {father_label}成績: {sire_perf['total_races']}戦{sire_perf['wins']}勝 複勝率{sire_perf['place_rate']:.1f}%")
                                        # 馬場状態別を追加（0戦のデータは表示しない）
                                        if sire_perf.get('by_condition'):
                                            for cond in sire_perf['by_condition']:
                                                # 0戦のデータは表示しない
                                                if cond['races'] > 0:
                                                    lines.append(f"      {cond['condition']}: {cond['races']}戦{cond['wins']}勝 複勝率{cond['place_rate']:.1f}%")
                                        entry['sire_performance'] = serialize_performance(sire_perf)

                            # 空行を追加（父と母父の成績を見やすく分離、bothモードのみ）
                            if mode == 'both' and sire and sire != 'データなし' and broodmare_sire and broodmare_sire != 'データなし':
                                lines.append("")

                            if mode != 'father':
                                # 母父の産駒成績を取得（broodmare または both の場合）
                                if broodmare_sire and broodmare_sire != 'データなし':
                                    bm_perf = analyzer.analyze_broodmare_sire_performance(
                                        broodmare_sire, venue_code, distance, track_type
                                    )
                                    if 'message' not in bm_perf:
                                        broodmare_label = course_label if distance else f"{course_label}"
                                        lines.append(f"    └ 母父 {broodmare_label}成績: {bm_perf['total_races']}戦{bm_perf['wins']}勝 複勝率{bm_perf['place_rate']:.1f}%")
                                        # 馬場状態別を追加（0戦のデータは表示しない）
                                        if bm_perf.get('by_condition'):
                                            for cond in bm_perf['by_condition']:
                                                # 0戦のデータは表示しない
                                                if cond['races'] > 0:
                                                    lines.append(f"      {cond['condition']}: {cond['races']}戦{cond['wins']}勝 複勝率{cond['place_rate']:.1f}%")
                                        entry['broodmare_performance'] = serialize_performance(bm_perf)

                        except Exception as e:
                            logger.debug(f"産駒成績取得エラー（{horse_name}）: {e}")
                            # エラーは無視（基本の血統表示は維持）

                else:
                    entry['status'] = 'no_data'
                    lines.append("  － 血統データなし")

                lines.append("")  # 1行空ける
                entries.append(entry)

            content = "\n".join(lines)

            # 分析データも返す（将来的な拡張用）
            analysis_data = {
                'status': 'success',
                'type': 'viewlogic_sire_analysis',
                'mode': mode,
                'venue': venue,
                'race_number': race_number,
                'distance': distance,
                'distance_label': course_suffix,
                'track_type': track_type,
                'is_local': is_local,
                'horses_count': len(horses),
                'entries': entries
            }

            return (content, analysis_data)

        except Exception as e:
            logger.error(f"種牡馬分析エラー: {e}")
            return (f"種牡馬分析中にエラーが発生しました: {str(e)}", None)

    def _generate_data_analysis(self, race_data: Dict[str, Any]) -> Tuple[str, Optional[Dict]]:
        """
        データ分析エンジン - 傾向分析と血統分析から上位3頭を抽出
        
        Returns:
            (content, analysis_data) のタプル
        """
        try:
            venue = race_data.get('venue', '')
            race_number = race_data.get('race_number', '')
            horses = race_data.get('horses', [])
            
            if not horses:
                return (f"{venue}{race_number}Rの出走馬データがありません。", None)
            
            # 各馬の複勝率データを収集
            horse_scores = {}  # {馬名: 最高複勝率}
            
            # 1. 傾向分析データを取得
            try:
                from services.viewlogic_engine import ViewLogicEngine
                viewlogic_engine = ViewLogicEngine()
                
                # タイムアウト設定
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("データ分析がタイムアウトしました")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(20)  # 20秒タイムアウト
                
                # 傾向分析実行
                trend_result = viewlogic_engine.analyze_course_trend(race_data)
                
                signal.alarm(0)  # タイムアウトリセット
                
                if trend_result.get('status') == 'success':
                    trends = trend_result.get('trends', {})
                    
                    # 馬のコース複勝率
                    if trends.get('horse_course_performance'):
                        for horse_data in trends['horse_course_performance']:
                            if horse_data.get('status') == 'found' and horse_data.get('total_runs', 0) > 0:
                                horse_name = horse_data.get('horse_name', '')
                                fukusho_rate = horse_data.get('fukusho_rate', 0.0)
                                if horse_name not in horse_scores:
                                    horse_scores[horse_name] = []
                                horse_scores[horse_name].append(fukusho_rate)
                    
                    # 騎手のコース複勝率（馬名とマッピング必要）
                    if trends.get('jockey_course_performance'):
                        # 馬と騎手のマッピングを作成
                        horse_jockey_map = {}
                        for i, horse in enumerate(horses):
                            if isinstance(horse, dict):
                                horse_name = horse.get('馬名', horse.get('name', ''))
                                jockey_name = horse.get('騎手', horse.get('jockey', ''))
                            else:
                                continue
                            if horse_name and jockey_name:
                                horse_jockey_map[jockey_name] = horse_name
                        
                        for jockey_data in trends['jockey_course_performance']:
                            if jockey_data.get('status') == 'found' and jockey_data.get('total_runs', 0) > 0:
                                jockey_name = jockey_data.get('jockey_name', '')
                                fukusho_rate = jockey_data.get('fukusho_rate', 0.0)
                                # この騎手が騎乗する馬を特定
                                if jockey_name in horse_jockey_map:
                                    horse_name = horse_jockey_map[jockey_name]
                                    if horse_name not in horse_scores:
                                        horse_scores[horse_name] = []
                                    horse_scores[horse_name].append(fukusho_rate)
                    
                    # 騎手の枠順別複勝率
                    if trends.get('jockey_post_performance'):
                        jockey_post_data = trends['jockey_post_performance']
                        if isinstance(jockey_post_data, dict):
                            for jockey_name, post_stats in jockey_post_data.items():
                                if isinstance(post_stats, dict):
                                    # 枠順別の複勝率を取得
                                    assigned_stats = post_stats.get('assigned_post_stats', {})
                                    if assigned_stats and isinstance(assigned_stats, dict):
                                        fukusho_rate = assigned_stats.get('fukusho_rate', 0.0)
                                        # 正規化処理
                                        if fukusho_rate > 100:
                                            fukusho_rate = fukusho_rate / 100
                                        elif fukusho_rate <= 1.0:
                                            fukusho_rate = fukusho_rate * 100
                                        fukusho_rate = min(fukusho_rate, 100.0)
                                        
                                        # 騎手が騎乗する馬を特定
                                        if jockey_name in horse_jockey_map:
                                            horse_name = horse_jockey_map[jockey_name]
                                            if horse_name not in horse_scores:
                                                horse_scores[horse_name] = []
                                            if fukusho_rate > 0:
                                                horse_scores[horse_name].append(fukusho_rate)
                
            except TimeoutError:
                logger.warning("傾向分析がタイムアウトしました")
            except Exception as e:
                logger.error(f"傾向分析エラー: {e}")
            
            # 2. 血統分析データを取得（産駒複勝率）
            try:
                # 地方競馬判定
                is_local = self._is_local_racing(venue)
                
                if not is_local and self.sire_analyzer:
                    # 会場コード取得
                    venue_codes = {
                        '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
                        '東京': '05', '中山': '06', '中京': '07', '京都': '08',
                        '阪神': '09', '小倉': '10'
                    }
                    venue_code = venue_codes.get(venue, '')
                    
                    # 距離取得
                    distance_value = race_data.get('distance', '')

                    raw_track_type = (
                        race_data.get('track_type')
                        or race_data.get('track')
                        or race_data.get('surface')
                        or race_data.get('course_type')
                    )
                    track_type = self._normalize_track_type(raw_track_type)

                    if not track_type and isinstance(distance_value, str):
                        if '芝' in distance_value:
                            track_type = '芝'
                        elif 'ダート' in distance_value or '砂' in distance_value:
                            track_type = 'ダート'
                        elif '障害' in distance_value:
                            track_type = '障害'

                    distance = distance_value
                    if isinstance(distance, str) and distance.endswith('m'):
                        distance = distance[:-1]
                    distance = str(distance)
                    
                    if venue_code and distance:
                        # 各馬の血統データから産駒複勝率を取得
                        dlogic_manager = self.dlogic_manager
                        
                        for horse in horses:
                            if isinstance(horse, dict):
                                horse_name = horse.get('馬名', horse.get('name', ''))
                            else:
                                horse_name = str(horse) if horse else ''
                            
                            if not horse_name:
                                continue
                            
                            # 血統データを取得
                            pedigree_data = self._get_horse_pedigree(dlogic_manager, horse_name)
                            
                            if pedigree_data:
                                sire = pedigree_data.get('sire', '')
                                broodmare_sire = pedigree_data.get('broodmare_sire', '')
                                
                                # 父の産駒複勝率
                                if sire and sire != 'データなし':
                                    try:
                                        sire_perf = self.sire_analyzer.analyze_sire_performance(
                                            sire, venue_code, distance, track_type
                                        )
                                        if 'message' not in sire_perf:
                                            place_rate = sire_perf.get('place_rate', 0.0)
                                            if horse_name not in horse_scores:
                                                horse_scores[horse_name] = []
                                            if place_rate > 0:
                                                horse_scores[horse_name].append(place_rate)
                                    except Exception as e:
                                        logger.debug(f"父馬産駒成績取得エラー（{sire}）: {e}")
                                
                                # 母父の産駒複勝率
                                if broodmare_sire and broodmare_sire != 'データなし':
                                    try:
                                        bm_perf = self.sire_analyzer.analyze_broodmare_sire_performance(
                                            broodmare_sire, venue_code, distance, track_type
                                        )
                                        if 'message' not in bm_perf:
                                            place_rate = bm_perf.get('place_rate', 0.0)
                                            if horse_name not in horse_scores:
                                                horse_scores[horse_name] = []
                                            if place_rate > 0:
                                                horse_scores[horse_name].append(place_rate)
                                    except Exception as e:
                                        logger.debug(f"母父産駒成績取得エラー（{broodmare_sire}）: {e}")
            
            except Exception as e:
                logger.error(f"血統分析エラー: {e}")
            
            # 3. 各馬の最高複勝率を計算
            final_scores = []
            for horse_name, rates in horse_scores.items():
                if rates:
                    max_rate = max(rates)
                    final_scores.append((horse_name, max_rate))
            
            # データが不足している馬も0点として追加
            existing_horses = set(horse_scores.keys())
            for horse in horses:
                if isinstance(horse, dict):
                    horse_name = horse.get('馬名', horse.get('name', ''))
                else:
                    horse_name = str(horse) if horse else ''
                
                if horse_name and horse_name not in existing_horses:
                    final_scores.append((horse_name, 0.0))
            
            # 4. ソートして上位3頭を選出
            final_scores.sort(key=lambda x: x[1], reverse=True)
            top_horses = final_scores[:3]
            
            # 5. 結果をフォーマット
            lines = []
            lines.append(f"{venue}{race_number}Rの傾向系分析から抽出したデータ上位3頭は以下の通りです。")
            
            # メダル絵文字を定義
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}

            for rank, (horse_name, rate) in enumerate(top_horses, 1):
                medal = medals.get(rank, "")
                lines.append(f"{medal}{rank}位 {horse_name}")
            
            content = "\n".join(lines)
            
            # 分析データも返す
            analysis_data = {
                'venue': venue,
                'race_number': race_number,
                'type': 'data_analysis',
                'top_horses': [(name, rate) for name, rate in top_horses],
                'total_analyzed': len(final_scores)
            }
            
            return (content, analysis_data)
            
        except Exception as e:
            logger.error(f"データ分析エラー: {e}")
            return (f"データ分析中にエラーが発生しました: {str(e)}", None)

    def _get_horse_pedigree(self, dlogic_manager, horse_name: str) -> Optional[Dict[str, str]]:
        """
        統合ナレッジファイルから馬の血統データを取得

        Args:
            dlogic_manager: DLogicRawDataManager インスタンス
            horse_name: 馬名

        Returns:
            血統データの辞書 {'sire': 父名, 'dam': 母名, 'broodmare_sire': 母父名}
        """
        try:
            # 馬の過去データを取得
            horse_data = dlogic_manager.get_horse_raw_data(horse_name)

            if not horse_data or 'races' not in horse_data:
                logger.debug(f"馬データが見つかりません（新馬の可能性）: {horse_name}")
                return None

            # 最新のレースから血統データを取得
            races = horse_data.get('races', [])
            if not races:
                return None

            # 最新レースのデータを使用
            latest_race = races[0]

            # フィールド29, 30, 31から血統データを取得
            pedigree = {
                'sire': latest_race.get('sire', latest_race.get('29', 'データなし')),
                'dam': latest_race.get('dam', latest_race.get('30', '')),
                'broodmare_sire': latest_race.get('broodmare_sire', latest_race.get('31', 'データなし'))
            }

            # 空文字の場合はNoneに変換
            if pedigree['dam'] == '':
                pedigree['dam'] = None

            return pedigree

        except Exception as e:
            logger.error(f"血統データ取得エラー ({horse_name}): {e}")
            return None
    
    async def process_nlogic_message(
        self,
        message: str,
        race_data: Dict[str, Any]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        N-Logic処理（オッズ予測）
        
        Args:
            message: ユーザーメッセージ
            race_data: レースデータ
        
        Returns:
            (応答テキスト, 分析データ)
        """
        try:
            venue = race_data.get('venue', '')

            engine = self.nlogic_engine
            engine_label = 'JRA'

            if self._is_local_racing(venue) and self.local_nlogic_engine:
                engine = self.local_nlogic_engine
                engine_label = '地方'

            if not engine:
                return ("⚠️ N-Logicエンジンが初期化されていません。現在利用できません。", None)

            logger.info("N-Logic処理開始 (engine=%s, venue=%s)", engine_label, venue)
            # 予測実行
            result = engine.predict_race(race_data)
            
            if result.get('status') != 'success':
                error_message = result.get('message', '不明なエラー')
                return (f"⚠️ N-Logic予測に失敗しました\n\n{error_message}", None)
            
            # カード形式で表示するため、簡易的なメッセージのみ
            content = f"🎯 N-Logic オッズ予測を生成しました（{result.get('total_horses')}頭）"
            
            # 分析データ（カード表示用）
            analysis_data = {
                'venue': result.get('venue'),
                'race_number': result.get('race_number'),
                'type': 'nlogic_prediction',
                'predictions': result.get('predictions'),
                'total_horses': result.get('total_horses')
            }
            
            return (content, analysis_data)
            
        except Exception as e:
            logger.error(f"N-Logic処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return (f"⚠️ N-Logic処理中にエラーが発生しました: {str(e)}", None)
    
    def _format_nlogic_result(self, result: Dict[str, Any]) -> str:
        """N-Logic結果のフォーマット"""
        try:
            lines = []
            lines.append("🎯 **N-Logic オッズ予測**")
            lines.append("")
            
            venue = result.get('venue', '不明')
            race_number = result.get('race_number', '')
            total_horses = result.get('total_horses', 0)
            
            if race_number:
                lines.append(f"📍 {venue} {race_number}R")
            else:
                lines.append(f"📍 {venue}")
            lines.append(f"🏇 出走頭数: {total_horses}頭")
            lines.append("")
            
            # 予測結果
            predictions = result.get('predictions', {})
            if not predictions:
                lines.append("⚠️ 予測結果がありません")
                return "\n".join(lines)
            
            # 順位順にソート
            sorted_predictions = sorted(
                predictions.items(),
                key=lambda x: x[1]['rank']
            )
            
            lines.append("### 【予測オッズ - 上位10頭】")
            lines.append("")
            
            for horse_name, pred in sorted_predictions[:10]:
                rank = pred['rank']
                odds = pred['odds']
                support_rate = pred['support_rate'] * 100
                
                if rank == 1:
                    emoji = '🥇'
                elif rank == 2:
                    emoji = '🥈'
                elif rank == 3:
                    emoji = '🥉'
                else:
                    emoji = f'**{rank}位**'
                
                lines.append(f"{emoji} **{horse_name}**")
                lines.append(f"　予測オッズ: **{odds}倍**　支持率: {support_rate:.1f}%")
                lines.append("")
            
            lines.append("---")
            lines.append("")
            lines.append("💡 **N-Logicについて**")
            lines.append("レース内の力関係を考慮したオッズ予測エンジンです。")
            lines.append("CatBoost + QuerySoftMax手法により、従来の単体予測より高精度な支持率を算出します。")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"N-Logic結果フォーマットエラー: {e}")
            return f"⚠️ 結果の表示に失敗しました: {str(e)}"
