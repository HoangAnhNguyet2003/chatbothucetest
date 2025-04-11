from database.db_connection import get_db_connection

def load_documents():
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, content FROM Documents")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Lỗi khi tải documents: {e}")
        return []

def load_chunks_by_documents(doc_ids):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        format_strings = ",".join(["?" for _ in doc_ids])
        query = f"SELECT chunk_id, document_id, chunk_text FROM Chunks WHERE document_id IN ({format_strings})"
        cursor.execute(query, doc_ids)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Lỗi khi tải chunks: {e}")
        return []
