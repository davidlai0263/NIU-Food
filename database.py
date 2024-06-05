import sqlite3
import threading
import pandas as pd

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.local = threading.local()

    @property
    def conn(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_file)
        return self.local.conn

    @property
    def cursor(self):
        if not hasattr(self.local, 'cursor'):
            self.local.cursor = self.conn.cursor()
        return self.local.cursor

    def create_table(self, table_name, columns):
        try:
            column_defs = ', '.join(columns)
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})")
            self.conn.commit()
            print(f"Table '{table_name}' created or already exists.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert_data(self, table_name, data):
        try:
            # 檢查是否已經存在該記錄
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = ?", (data[0],))
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # 更新記錄
                self.cursor.execute(f"UPDATE {table_name} SET status = ?, lat = ?, lng = ? WHERE id = ?", data[1:] + (data[0],))
            else:
                # 插入新記錄
                placeholders = ', '.join(['?' for _ in range(len(data))])
                self.cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", data)
            
            self.conn.commit()
            return data
        except sqlite3.Error as e:
            print(f"Error inserting/updating data: {e}")
            return None

    def read_data(self, table_name):
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error reading data: {e}")
            return []

    def table_exists(self, table_name):
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            return self.cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            print(f"Error checking table existence: {e}")
            return False

    def close_connection(self):
        self.conn.close()

class CSVData:
    column = {
        'url': 1,
        'name': 2,
        'star': 3,
        'review': 4,
        'typ': 6,
        'img': 8,
        'location': 9,
        'keyword': 11,
    }
    def __init__(self, path):
        self.csv_data = pd.read_csv(path)

    def get_data(self):
        return self.csv_data.values.tolist()
    
    def get_cell_by_key(self, data, key):
        if key in self.column:
            return data[self.column[key]]
        return None