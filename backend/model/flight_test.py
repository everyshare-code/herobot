import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_access_token():
    client_id = os.getenv('AMADEUS_CLIENT_ID')
    client_secret = os.getenv('AMADEUS_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("환경 변수가 제대로 설정되지 않았습니다.")
        return None

    url = 'https://api.amadeus.com/v1/security/oauth2/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        access_token = response.json().get('access_token')
        if not access_token:
            print(f"토큰 응답에서 액세스 토큰을 찾을 수 없습니다: {response.json()}")
        return access_token
    except requests.exceptions.RequestException as e:
        print(f"토큰 생성 중 오류 발생: {e}")
        if e.response:
            print(f"응답 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        return None


if __name__ == "__main__":
    token = get_access_token()
    print(f"Access Token: {token}")
