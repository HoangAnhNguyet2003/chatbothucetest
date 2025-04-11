import logging
import os

from configs.settings import UPLOAD_FOLDER
from database.create_database import get_db_connection
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)
app = Flask(__name__)

def is_file_in_database(filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT COUNT(*) FROM Documents WHERE filename = ?"
        cursor.execute(query, (filename,))
        result = cursor.fetchone()[0] > 0
        return result
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra file trong DB: {e}")
        return False
    finally:
        conn.close()

def save_all_txt_in_folder():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if is_file_in_database(file_path):
                continue
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            query = "INSERT INTO Documents (filename, content) VALUES (?, ?)"
            cursor.execute(query, (file_path, content))
            conn.commit()
            logger.info(f"Đã lưu file {file_path} vào DB.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu file vào DB: {e}")
    finally:
        conn.close()

def read_and_chunk_files_from_folder(chunk_size=768, overlap=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, content FROM Documents")
        documents = cursor.fetchall()
        
        for document_id, content in documents:
            cursor.execute("SELECT COUNT(*) FROM Chunks WHERE document_id = ?", (document_id,))
            if cursor.fetchone()[0] > 0:
                logger.info(f"Document ID {document_id} đã được chia nhỏ, bỏ qua.")
                continue  # Bỏ qua nếu đã chia
            
            # Chia nhỏ nội dung
            chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size - overlap)]
            logger.info(f"Đã chia nhỏ document ID {document_id} thành {len(chunks)} chunks.")
            for chunk in chunks:
                cursor.execute("INSERT INTO Chunks (document_id, chunk_text) VALUES (?, ?)", (document_id, chunk))
            conn.commit()
            logger.info(f"Đã lưu {len(chunks)} chunks cho document ID {document_id}.")
    except Exception as e:
        logger.error(f"Lỗi khi chia nhỏ file: {e}")
    finally:
        conn.close()