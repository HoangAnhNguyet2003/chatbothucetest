import pyodbc
from configs.settings import DB_CONFIG

def get_db_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={DB_CONFIG['DRIVER']};"
            f"SERVER={DB_CONFIG['SERVER']};"
            f"DATABASE={DB_CONFIG['DATABASE']};"
            f"Trusted_Connection={DB_CONFIG['Trusted_Connection']};"
        )
        return conn
    except Exception as e:
        print(f"Lỗi kết nối DB: {e}")
        return None
