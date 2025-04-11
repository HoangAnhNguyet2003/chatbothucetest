import os
import pickle
import torch
from transformers import AutoTokenizer, AutoModel
from database.db_connection import get_db_connection
from configs.settings import EMBEDDINGS_PATH
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load PhoBERT
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base").to(device)

def save_embeddings_to_pkl():
    if os.path.exists(EMBEDDINGS_PATH):
        logger.info(f"Embeddings đã tồn tại tại {EMBEDDINGS_PATH}, bỏ qua!")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT chunk_id, document_id, chunk_text FROM Chunks")
        rows = cursor.fetchall()

        if not rows:
            logger.warning("Không có dữ liệu trong bảng Chunks.")
            return

        embeddings = []

        for chunk_id, document_id, chunk_text in rows:
            tokens = tokenizer(chunk_text, padding=True, truncation=True, max_length=256, return_tensors="pt")
            tokens = {key: val.to(device) for key, val in tokens.items()}

            with torch.no_grad():
                outputs = model(**tokens)
                sentence_embedding = torch.mean(outputs.last_hidden_state, dim=1).squeeze(0).cpu().numpy()

            embeddings.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "embedding": sentence_embedding
            })

        with open(EMBEDDINGS_PATH, "wb") as f:
            pickle.dump(embeddings, f)
        logger.info(f"Đã lưu embeddings thành công tại {EMBEDDINGS_PATH}")

    except Exception as e:
        logger.error(f"Lỗi khi lưu embeddings: {e}")

    finally:
        conn.close()
