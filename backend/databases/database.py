from sqlalchemy import create_engine, Table, MetaData, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict
import csv
from functools import wraps
from backend.core.config import settings

metadata = MetaData()

def db_connect(func):
    @wraps(func)
    def with_connection(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            self.session.commit()
            return result
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error: {e}")
            return None
        finally:
            self.session.close()
    return with_connection

class Database:
    def __init__(self):
        self.engine = self.create_engine()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_engine(self):
        return create_engine(settings.CONNECTION_STRING, pool_size=10, pool_pre_ping=True)

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
    def insert_datas(self, table: str, data: List[Dict]) -> int:
        if not data:
            return 0

        table_ref = Table(table, metadata, autoload_with=self.engine)
        self.session.bulk_insert_mappings(table_ref, data)
        print(f"Data inserted into {table}")
        return len(data)

    @db_connect
    def insert_data(self, table: str, data: Dict) -> int:
        table_ref = Table(table, metadata, autoload_with=self.engine)
        ins = table_ref.insert().values(**data)
        self.session.execute(ins)
        print(f"Data inserted into {table}")
        return 1

    @db_connect
    def fetch_data(self, table: str, params:Dict=None, columns:str='*') -> List:
        table_ref = Table(table, metadata, autoload_with=self.engine)
        selected_columns = [table_ref.c[col] for col in columns.split(', ')] if columns != '*' else [table_ref]

        stmt = select(*selected_columns)
        first_key = next(iter(params))
        if params:
            stmt = stmt.where(table_ref.c[first_key] == params[first_key])
        else:
            params={}
        result = self.session.execute(stmt, params).fetchall()
        print(f"result:{result}")
        return result

    @db_connect
    def update_data(self, table:str, data: Dict, where_clause:str) -> int:
        table_ref = Table(table, metadata, autoload_with=self.engine)
        update_stmt = table_ref.update().where(text(where_clause)).values(**data)
        self.session.execute(update_stmt)
        print(f"Data updated in {table}")
        return 1

    @db_connect
    def delete_data(self, table:str, where_clause:str) -> int:
        table_ref = Table(table, metadata, autoload_with=self.engine)
        delete_stmt = table_ref.delete().where(text(where_clause))
        self.session.execute(delete_stmt)
        print(f"Data deleted from {table}")
        return 1

# if __name__ == "__main__":
    # db = Database()
    # data = db.load_data_as_dict("/Users/everyshare/PycharmProjects/herobot/backend/datas/flights/airports_dataset.csv")
    # print(data)
    # db.insert_datas("airports", data)
