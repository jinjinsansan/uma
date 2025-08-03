#!/usr/bin/env python3
"""
JV-Linkデータ取得スクリプト（Windows専用）
WSL/Linux環境からは直接実行不可のため、Windows側で実行してJSONで出力
"""
import json
import os
from datetime import datetime, date
from typing import Dict, List, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JVLinkDataFetcher:
    """JV-Linkデータ取得クラス"""
    
    def __init__(self):
        self.jv = None
        self.data_cache = {}
        
    def initialize(self) -> bool:
        """JV-Link初期化"""
        try:
            import win32com.client
            self.jv = win32com.client.Dispatch("JVDTLab.JVLink")
            
            result = self.jv.JVInit("UNKNOWN")
            if result == 0:
                logger.info("✅ JV-Link初期化成功")
                return True
            else:
                logger.error(f"❌ JV-Link初期化エラー: {result}")
                return False
                
        except ImportError:
            logger.error("❌ win32com.client が見つかりません")
            logger.error("   インストール: pip install pywin32")
            return False
        except Exception as e:
            logger.error(f"❌ JV-Link初期化エラー: {e}")
            return False
    
    def fetch_today_races(self) -> Dict[str, Any]:
        """今日のレースデータ取得"""
        if not self.jv:
            logger.error("JV-Linkが初期化されていません")
            return {}
        
        try:
            logger.info("📊 今週レースデータ取得開始")
            
            # 今週データ取得
            fromtime = "00000000000000"
            result = self.jv.JVOpen("RACE", fromtime, 4)  # option=4は今週データ
            
            if result != 0:
                logger.error(f"❌ データ取得エラー: {result}")
                return {}
            
            races_data = {
                "date": date.today().strftime('%Y-%m-%d'),
                "lastUpdate": datetime.now().isoformat(),
                "racecourses": []
            }
            
            racecourses = {}
            race_count = 0
            
            # データ読み取り
            while True:
                result = self.jv.JVRead()
                
                if result == -1:  # 終了
                    break
                elif result == 0:  # 正常
                    data = self.jv.GetLastReadData()
                    if data:
                        race_count += 1
                        # レースデータを解析
                        race_info = self._parse_race_data(data)
                        if race_info:
                            self._add_race_to_courses(racecourses, race_info)
                            
                elif result == -3:  # ダウンロード中
                    logger.info("⏳ ダウンロード中...")
                    import time
                    time.sleep(1)
                    continue
                else:
                    logger.warning(f"⚠️  読み取り結果: {result}")
                    break
            
            # 競馬場データを整形
            races_data["racecourses"] = list(racecourses.values())
            
            logger.info(f"📊 取得完了: {race_count}件のレースデータ")
            
            # クローズ
            self.jv.JVClose()
            
            return races_data
            
        except Exception as e:
            logger.error(f"❌ データ取得エラー: {e}")
            return {}
    
    def _parse_race_data(self, data: str) -> Dict[str, Any]:
        """レースデータ解析"""
        try:
            # JV-Dataの仕様に基づいてデータを解析
            # ここでは簡易版として基本情報のみ抽出
            
            if len(data) < 50:
                return None
                
            # レコード種別IDを確認
            record_type = data[:2]
            
            if record_type == "RA":  # レース詳細
                race_info = {
                    "recordType": "race_detail",
                    "raceCode": data[2:18].strip(),
                    "kaisaiYear": data[18:22].strip(),
                    "kaisaiMonthDay": data[22:26].strip(),
                    "raceNumber": data[30:32].strip(),
                    "raceName": data[50:100].strip(),
                    "distance": data[100:104].strip(),
                    "trackCode": data[104:106].strip()
                }
                return race_info
                
            elif record_type == "SE":  # 馬毎レース情報
                horse_info = {
                    "recordType": "horse_entry",
                    "raceCode": data[2:18].strip(),
                    "horseNumber": data[30:32].strip(),
                    "horseName": data[50:86].strip(),
                    "jockeyName": data[200:208].strip(),
                    "weight": data[150:153].strip(),
                    "horseWeight": data[160:163].strip()
                }
                return horse_info
                
            return None
            
        except Exception as e:
            logger.error(f"データ解析エラー: {e}")
            return None
    
    def _add_race_to_courses(self, racecourses: Dict, race_info: Dict):
        """競馬場データに追加"""
        try:
            race_code = race_info.get("raceCode", "")
            if len(race_code) >= 10:
                course_code = race_code[8:10]  # 競馬場コード
                
                if course_code not in racecourses:
                    racecourses[course_code] = {
                        "courseId": course_code,
                        "name": self._get_course_name(course_code),
                        "weather": "晴",
                        "trackCondition": "良",
                        "races": []
                    }
                
                # レース情報を追加（重複チェック）
                race_number = race_info.get("raceNumber", "")
                existing_race = None
                for race in racecourses[course_code]["races"]:
                    if race.get("raceNumber") == race_number:
                        existing_race = race
                        break
                
                if not existing_race and race_info.get("recordType") == "race_detail":
                    race_data = {
                        "raceId": f"{course_code}_{race_number}r",
                        "raceNumber": int(race_number) if race_number.isdigit() else 0,
                        "raceName": race_info.get("raceName", ""),
                        "distance": f"{race_info.get('distance', '')}m",
                        "track": self._get_track_type(race_info.get("trackCode", "")),
                        "horses": []
                    }
                    racecourses[course_code]["races"].append(race_data)
                
                # 出走馬情報を追加
                elif race_info.get("recordType") == "horse_entry" and existing_race:
                    horse_data = {
                        "number": int(race_info.get("horseNumber", "0")),
                        "name": race_info.get("horseName", ""),
                        "jockey": race_info.get("jockeyName", ""),
                        "weight": f"{race_info.get('weight', '')}kg",
                        "horseWeight": f"{race_info.get('horseWeight', '')}kg"
                    }
                    existing_race["horses"].append(horse_data)
                    
        except Exception as e:
            logger.error(f"競馬場データ追加エラー: {e}")
    
    def _get_course_name(self, course_code: str) -> str:
        """競馬場名取得"""
        course_names = {
            "01": "札幌競馬場",
            "02": "函館競馬場", 
            "03": "福島競馬場",
            "04": "新潟競馬場",
            "05": "東京競馬場",
            "06": "中山競馬場",
            "07": "中京競馬場",
            "08": "京都競馬場",
            "09": "阪神競馬場",
            "10": "小倉競馬場"
        }
        return course_names.get(course_code, f"競馬場{course_code}")
    
    def _get_track_type(self, track_code: str) -> str:
        """トラック種別取得"""
        track_types = {
            "10": "芝",
            "20": "ダート",
            "21": "砂",
            "22": "ポリトラック"
        }
        return track_types.get(track_code, "芝")
    
    def save_to_json(self, data: Dict, filename: str = "jvlink_races_data.json"):
        """JSONファイルに保存"""
        try:
            output_path = os.path.join(os.path.dirname(__file__), "data", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ データ保存完了: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ ファイル保存エラー: {e}")
            return None

def main():
    """メイン処理"""
    logger.info("🏇 JV-Linkデータ取得開始")
    
    fetcher = JVLinkDataFetcher()
    
    if not fetcher.initialize():
        logger.error("❌ JV-Link初期化失敗")
        return
    
    # 今日のレースデータ取得
    races_data = fetcher.fetch_today_races()
    
    if races_data:
        # JSONファイルに保存
        output_file = fetcher.save_to_json(races_data)
        if output_file:
            logger.info("🎯 JV-Linkデータ取得完了")
            logger.info(f"   ファイル: {output_file}")
        else:
            logger.error("❌ データ保存失敗")
    else:
        logger.error("❌ レースデータ取得失敗")

if __name__ == "__main__":
    main()