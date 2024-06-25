from typing import Dict, Optional
from backend.databases.database import Database
def summarize_flight_information(db: Database, flight_data: Dict) -> str:
    origin_code = flight_data.get('originCode', '')
    origin = get_airports_name(db, origin_code)
    destination_code = flight_data.get('destinationCode', '')
    destination = get_airports_name(db, destination_code)
    departure_date = flight_data.get('departureDate', '알 수 없음')
    departure_time = flight_data.get('departureTime', '알 수 없음')
    arrival_time = flight_data.get('arrivalTime', '알 수 없음')
    price = int(float(flight_data.get('price', 0)))
    airline = get_airline_data(db, flight_data.get('airlineCode', '알 수 없음'))
    flight_data['airline'] = airline
    summary = (f"{origin}({origin_code})에서 {destination}({destination_code})으로 가는 항공편이 "
               f"{departure_date}에 출발하여 {departure_time}에 출발, {arrival_time}에 도착합니다. "
               f"가격은 {price}원이며, 운항은 {airline}에서 담당합니다.")
    return summary

def get_airline_data(db: Database, airline_code: str) -> Optional[Dict]:
    try:
        return db.fetch_data(table="carriers", where_clause=f"where carrierCode = '{airline_code}'")[0]
    except IndexError:
        print(f"No data found for airline code: {airline_code}")
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def get_airports_name(db: Database, iata: str):
    try:
        return db.fetch_data(table="airports", columns="AIRPORT_NAME", where_clause=f"where IATA = '{iata}'")[0]
    except IndexError:
        print(f"No data found for airline code: {iata}")
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None


if __name__ == "__main__":
    db = Database()
    name = get_airports_name(db, 'ICN')
    print(name)