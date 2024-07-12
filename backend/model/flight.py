import requests
from typing import Dict, List
from backend.core.config import settings
from backend.databases.database import Database
from backend.utils import (
    parse_flight_info,
    summarize_flight_information,
    validate_date
)
from backend.model.client import Client

class SkyscannerAPI:
    def __init__(self):
        self.base_url = "https://sky-scanner3.p.rapidapi.com/flights/search-one-way"
        self.headers = {
            'x-rapidapi-key': settings.X_RAPIDAPI_KEY,
            'x-rapidapi-host': settings.X_RAPIDAPI_HOST
        }

    def get_flight_info(self, client_info: Dict) -> List[Dict]:
        querystring = {
            "fromEntityId": client_info['origin_location_code'],
            "toEntityId": client_info['destination_location_code'],
            "departDate": validate_date(client_info['departure_date']),
            "currency": "KRW"
        }
        response = requests.get(self.base_url, headers=self.headers, params=querystring).json()
        print(response)
        if not response.get('status', False):
            return []
        itineraries = response['data']['itineraries']
        return parse_flight_info(itineraries)

    def get_cheapest_flight_info(self, db:Database, client_info: Dict) -> str:
        flight_info_list = self.get_flight_info(client_info)
        return summarize_flight_information(db, flight_info_list)


if __name__ == "__main__":
    import ssl
    # SSL 인증서 검증을 비활성화하는 컨텍스트 생성
    ssl._create_default_https_context = ssl._create_unverified_context

    client_info = {
        "fromEntityId": "PARI",
        "toEntityId": "MSY",
        "departDate": "2024-08-15",
    }

    db = Database()

    api = SkyscannerAPI()
    cheapest_flight_info = api.get_cheapest_flight_info(db, client_info)
    print(cheapest_flight_info)