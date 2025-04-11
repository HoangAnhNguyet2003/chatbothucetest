import numpy as np
import pandas as pd
import pyodbc
import os
import pickle
import torch
from transformers import AutoTokenizer, AutoModel
from rank_bm25 import BM25Okapi
import requests

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base").to(device)

FAISS_MAPPING_PATH = "../embeddings.pkl"

def get_db_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=DESKTOP-CSDJ6DE\\SQLEXPRESS;"
            "DATABASE=chatbot;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        return None

def load_documents():
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, content FROM Documents")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
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
        return []

def load_faiss_mapping():
    if not os.path.exists(FAISS_MAPPING_PATH):
        return None
    try:
        with open(FAISS_MAPPING_PATH, "rb") as f:
            mapping = pickle.load(f)
        return mapping
    except Exception as e:
        return None

mapping = load_faiss_mapping()
documents = load_documents()
if not documents:
    exit()

document_texts = [doc.content for doc in documents]
tokenized_docs = [text.split() for text in document_texts]
bm25 = BM25Okapi(tokenized_docs)

query = input("🔍 Nhập câu hỏi: ").strip()
if not query:
    exit()

tokenized_query = query.split()
bm25_scores = bm25.get_scores(tokenized_query)
top_15_idx = np.argsort(bm25_scores)[::-1][:15]

relevant_docs = [documents[i] for i in top_15_idx]
relevant_doc_ids = [doc.id for doc in relevant_docs]

relevant_chunks = load_chunks_by_documents(relevant_doc_ids)
if not relevant_chunks:
    exit()

chunk_texts = [chunk.chunk_text for chunk in relevant_chunks]
chunk_ids = [chunk.chunk_id for chunk in relevant_chunks]

tokens = tokenizer(query, padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
with torch.no_grad():
    query_embedding = torch.mean(model(**tokens).last_hidden_state, dim=1).squeeze(0).cpu().numpy()
query_embedding = query_embedding / np.linalg.norm(query_embedding)

if mapping is None:
    top_20_idx = np.argsort(bm25_scores[top_15_idx])[-20:]
    exit()

relevant_embeddings, relevant_chunk_ids = [], []
for chunk in relevant_chunks:
    for info in mapping:
        if info["chunk_id"] == chunk.chunk_id:
            relevant_embeddings.append(info["embedding"])
            relevant_chunk_ids.append(chunk.chunk_id)

if not relevant_embeddings:
    exit()

relevant_embeddings = np.array(relevant_embeddings, dtype=np.float32)

phoBert_scores = np.dot(relevant_embeddings, query_embedding)
bm25_scores_selected = np.array([bm25_scores[i % 25] for i in range(len(phoBert_scores))])
combined_scores = 0.45 * bm25_scores_selected + 0.55 * phoBert_scores
top_20_idx = np.argsort(combined_scores)[::-1][:20]

def call_gpt_api(prompt):
    api_key = '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'
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700 
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None

top_chunks_content = [chunk_texts[i] for i in top_20_idx]

if top_chunks_content:
    prompt = f"Dựa trên các thông tin:\n{'. '.join(top_chunks_content)}\nHãy trả lời câu hỏi: {query} như một trợ lý của trường đại học Xây Dựng. Hãy trả lời chính xác không được tự ý sửa thông tin, nếu không có hãy đưa ra các thông tin liên lạc liên quan"
    response = call_gpt_api(prompt)
    print("\n🔹 Câu trả lời:", response if response else "Không tìm thấy văn bản nào liên quan.")
else:
    print("\n⚠️ Không tìm thấy văn bản nào phù hợp.")