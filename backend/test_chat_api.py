import requests
import json

def test_chat_api():
    """チャットAPIをテスト"""
    url = "http://localhost:8002/api/chat/message"
    
    payload = {
        "message": "本日の東京3Rの指数を出して",
        "history": []
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_chat_api() 