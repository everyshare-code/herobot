from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv
import certifi
from backend.databases.database import Database
from typing import Dict, List, Optional
from backend.utils.amadeus_util import summarize_flight_information, get_airline_data, get_airports_name


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
                    'maxFlightOffers': 1,
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
                flight_offer = response.result['data'][0]
                airline_code = flight_offer['itineraries'][0]['segments'][0]['carrierCode']
                first_segment = flight_offer['itineraries'][0]['segments'][0]
                last_segment = flight_offer['itineraries'][0]['segments'][-1]
                return summarize_flight_information(db, {
                    'originCode': flight_offer['itineraries'][0]['segments'][0]['departure']['iataCode'],
                    'destinationCode': flight_offer['itineraries'][0]['segments'][-1]['arrival']['iataCode'],
                    'departureDate': flight_offer['itineraries'][0]['segments'][0]['departure']['at'].split('T')[0],
                    'departureTime': first_segment['departure']['at'].split('T')[1],
                    'arrivalTime': last_segment['arrival']['at'].split('T')[1],
                    'price': flight_offer['price']['total'],
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




if __name__ == "__main__":

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
    response = amadeus.search_lowest_fare_flight(db, client_info)
    print(response)
