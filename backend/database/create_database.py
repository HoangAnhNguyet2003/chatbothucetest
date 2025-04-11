import logging
from database.db_connection import get_db_connection

logger = logging.getLogger(__name__)

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        create_documents_table = '''
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Documents')
        BEGIN
            CREATE TABLE Documents (
                id INT IDENTITY(1,1) PRIMARY KEY,
                filename NVARCHAR(255) UNIQUE,
                content NTEXT
            );
        END;
        '''

        create_chunks_table = '''
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Chunks')
        BEGIN
            CREATE TABLE Chunks (
                chunk_id INT IDENTITY(1,1) PRIMARY KEY,
                document_id INT,
                chunk_text NVARCHAR(MAX),
                FOREIGN KEY (document_id) REFERENCES Documents(id) ON DELETE CASCADE
            );
        END;
        '''

        cursor.execute(create_documents_table)
        cursor.execute(create_chunks_table)
        conn.commit()
        logger.info("Tạo bảng thành công.")
    except Exception as e:
        logger.error(f"Lỗi khi tạo bảng: {e}")
    finally:
        conn.close() 