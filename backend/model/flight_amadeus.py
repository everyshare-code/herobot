from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv
import certifi
from backend.databases.database import Database
from typing import Dict, Optional
from backend.utils.flight_util import summarize_flight_information

class AmadeusAPI:
    def __init__(self):
        load_dotenv()  # 환경 변수 로드
        self.client_id = os.getenv('AMADEUS_CLIENT_ID')
        self.client_secret = os.getenv('AMADEUS_CLIENT_SECRET')

        if not self.client_id or not self.client_secret:
            raise ValueError("환경 변수가 제대로 설정되지 않았습니다.")

        # Amadeus 클라이언트 초기화 (프로덕션 환경)
        self.amadeus = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            hostname='production',  # 프로덕션 환경을 명확히 설정
            log_level='debug',
            ssl_ca_file=certifi.where()
        )

    def search_lowest_fare_flight(self, db: Database, client_info: Dict) -> Optional[str]:
        try:
            travelers = [{
                'id': str(i + 1),
                'travelerType': 'ADULT',
                'fareOptions': ['STANDARD']
            } for i in range(client_info['adults'])]

            search_params = {
                'originDestinations': [{
                    'id': '1',
                    'originLocationCode': client_info['originLocationCode'],
                    'destinationLocationCode': client_info['destinationLocationCode'],
                    'departureDateTimeRange': {
                        'date': client_info['departureDate'],
                    }
                }],
                'travelers': travelers,
                'sources': ['GDS'],
                'searchCriteria': {
                    'maxFlightOffers': 250,  # 최대 항공권 수를 설정하여 더 많은 결과를 가져옵니다.
                    'flightFilters': {
                        'cabinRestrictions': [{
                            'cabin': 'ECONOMY',
                            'coverage': 'MOST_SEGMENTS',
                            'originDestinationIds': ['1']
                        }]
                    }
                },
                'currencyCode': 'KRW'
            }

            response = self.amadeus.shopping.flight_offers_search.post(body=search_params)
            print(response.result)  # 응답 데이터 확인

            if response.result and response.result.get('data'):
                flight_offers = response.result['data']
                # 최저가 항공권을 선택하는 로직 추가
                lowest_fare = float('inf')
                lowest_fare_offer = None

                for offer in flight_offers:
                    price = float(offer['price']['total'])
                    if price < lowest_fare:
                        lowest_fare = price
                        lowest_fare_offer = offer

                if lowest_fare_offer:
                    airline_code = lowest_fare_offer['itineraries'][0]['segments'][0]['carrierCode']
                    first_segment = lowest_fare_offer['itineraries'][0]['segments'][0]
                    last_segment = lowest_fare_offer['itineraries'][0]['segments'][-1]
                    return summarize_flight_information(db, {
                        'originCode': lowest_fare_offer['itineraries'][0]['segments'][0]['departure']['iataCode'],
                        'destinationCode': lowest_fare_offer['itineraries'][0]['segments'][-1]['arrival']['iataCode'],
                        'departureDate': lowest_fare_offer['itineraries'][0]['segments'][0]['departure']['at'].split('T')[0],
                        'departureTime': first_segment['departure']['at'].split('T')[1],
                        'arrivalTime': last_segment['arrival']['at'].split('T')[1],
                        'price': lowest_fare_offer['price']['total'],
                        'airlineCode': airline_code,
                        'airline': "",
                        'airlineLogo': f'https://pic.tripcdn.com/airline_logo/3x/{airline_code.lower()}.webp'
                    })

        except ResponseError as error:
            print(f"API 호출 중 오류 발생: {error}")
            if error.response:
                print(f"응답 코드: {error.response.status_code}")
                print(f"응답 내용: {error.response.result}")
            return "검색된 정보가 없습니다."


    def search_cheapest_date(self, origin: str, destination: str, start_date: str, end_date: str) -> Optional[Dict]:
        try:
            response = self.amadeus.shopping.flight_dates.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=start_date,
                returnDate=end_date
            )

            print(response.result)  # 응답 데이터 확인

            if response.result and response.result.get('data'):
                return response.result['data']

        except ResponseError as error:
            print(f"API 호출 중 오류 발생: {error}")
            if error.response:
                print(f"응답 코드: {error.response.status_code}")
                print(f"응답 내용: {error.response.result}")
            return None

if __name__ == "__main__":
    from backend.core.config import Settings
    settings = Settings()
    import ssl
    # SSL 인증서 검증을 비활성화하는 컨텍스트 생성
    ssl._create_default_https_context = ssl._create_unverified_context
    db = Database()
    client_info = {
        "adults": 1,
        "originLocationCode": "ICN",
        "destinationLocationCode": "DAD",
        "departureDate": "2024-09-04"
    }

    amadeus = AmadeusAPI()
    # 최저가 항공권 조회
    lowest_fare_response = amadeus.search_lowest_fare_flight(db, client_info)
    print(lowest_fare_response)

    # 최저가 날짜 조회
    cheapest_date_response = amadeus.search_cheapest_date("ICN", "DAD", "2024-09-01", "2024-09-30")
    print(cheapest_date_response)
