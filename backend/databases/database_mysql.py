from mysql.connector import Error, pooling
from backend.core.config import settings
import csv
from typing import List, Dict
from dotenv import load_dotenv
import os
from functools import wraps
from backend.model.messages import Message

load_dotenv()

def db_connect(func):
    @wraps(func)
    def with_connection(instance, *args, **kwargs):
        connection = None
        cursor = None
        try:
            connection = instance.connection_pool.get_connection()
            if connection.is_connected():
                print("데이터베이스 연결 성공")
                cursor = connection.cursor(dictionary=True)
                result = func(instance, cursor, *args, **kwargs)
                connection.commit()
                return result
        except Error as e:
            print(f"Error: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    return with_connection

class Database:
    def __init__(self):
        config_path = os.path.join(os.getenv("ROOT_DIR"), os.getenv("DB_CONFIG_PATH"))
        self.connection_pool = None
        self.create_connection_pool()


    def create_connection_pool(self):
        try:
            db_config = settings.config
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="herobot_db_pool",
                pool_size=10,
                pool_reset_session=True,
                **db_config
            )
        except Error as e:
            print(e)
    def insert_message(self, cursor, session_id: str, message: Message):
        role = message.sender
        content = message.message

    def load_data(self, filename='') -> List:
        data = []
        with open(filename, 'rt') as f:
            csv_data = csv.reader(f)
            for row in csv_data:
                data.append(row)
        return data

    def load_data_as_dict(self, filename: str) -> List[Dict]:
        data = []
        with open(filename, 'rt') as f:
            csv_data = csv.DictReader(f)
            for row in csv_data:
                data.append(row)
        return data

    @db_connect
    def insert_datas(self, cursor, table, data: List[Dict]) -> int:
        if not data:
            return 0

        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["%s"] * len(data[0]))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        values = [list(row.values()) for row in data]
        cursor.executemany(sql, values)
        print(f"Data inserted into {table}")
        return cursor.rowcount
    @db_connect
    def insert_data(self, cursor, table, data) -> int:
        placeholders = ", ".join(["%s"] * len(data))
        columns = ", ".join(data.keys())
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        print(f"Data inserted into {table}")
        return cursor.rowcount

    @db_connect
    def fetch_data(self, cursor, table, where_clause="", params=None, columns='*') -> List:
        sql = f"SELECT {columns} FROM {table} {where_clause}"
        cursor.execute(sql, params or ())
        return cursor.fetchall()

    @db_connect
    def update_data(self, cursor, table, data, where_clause) -> int:
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        cursor.execute(sql, list(data.values()))
        print(f"Data updated in {table}")
        return cursor.rowcount

    @db_connect
    def delete_data(self, cursor, table, where_clause) -> int:
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        cursor.execute(sql)
        print(f"Data deleted from {table}")
        return cursor.rowcount


if __name__ == "__main__":
    db = Database()
    data = db.load_data_as_dict("/Users/everyshare/PycharmProjects/herobot/backend/datas/flights/airports_dataset.csv")
    print(data)
    # db.insert_datas("airports", data)



