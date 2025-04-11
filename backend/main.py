from flask import Flask, request, jsonify
import re
import logging
from database.data_loader import load_documents, load_chunks_by_documents
from retrieval.bm25_retriever import get_bm25_retriever, retrieve_top_k
from retrieval.embedding_retriever import load_faiss_mapping, get_embedding
from models.gpt_api import call_gpt_api
from utils.chitchat_detector import ChitChatDetector
import numpy as np
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Khởi tạo lịch sử chat
chat_history = []
MAX_HISTORY_LENGTH = 10

def create_prompt(history, chunks, query):
    history_prompt = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in history])
    formatted_chunks = "\n".join([f"### CHUNK_ID: {chunk_id}\n{text}" for chunk_id, text in chunks])
    return (
        f"Dựa trên lịch sử chat:\n{history_prompt}\n\n"
        f"Dựa trên các thông tin sau:\n{formatted_chunks}\n\n"
        f"Hãy trả lời câu hỏi: {query} như trợ lý ảo của đại học xây dựng, không được phép sửa đổi thành thông tin sai lệch. Nếu không có câu trả lời hãy đưa ra các thông tin liên hệ.\n"
        f"**Lưu ý:** Nếu có thể, hãy đề cập đến `CHUNK_ID` mà bạn tham khảo."
    )

@app.route('/api/chat', methods=['POST'])
def chat():
    chitchat_detector = ChitChatDetector()
    documents = load_documents()
    bm25 = get_bm25_retriever(documents)

    data = request.json
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"response": "Không có câu hỏi."}), 400

    if chitchat_detector.is_chitchat(query):
        logging.info("ChitChat detected")
        return jsonify({"response": "Xin chào! Tôi có thể giúp gì cho bạn?"}), 200

    try:
        # Lấy các tài liệu liên quan
        top_15_idx, bm25_scores = retrieve_top_k(bm25, query)
        relevant_docs = [documents[i] for i in top_15_idx]
        relevant_doc_ids = [doc.id for doc in relevant_docs]

        relevant_chunks = load_chunks_by_documents(relevant_doc_ids)
        if not relevant_chunks:
            return jsonify({"response": "Không tìm thấy văn bản nào phù hợp."}), 404

        chunk_id_to_text = {chunk.chunk_id: chunk.chunk_text for chunk in relevant_chunks}
        mapping = load_faiss_mapping()

        if isinstance(mapping, np.ndarray):
            relevant_embeddings = mapping
        elif isinstance(mapping, list):
            relevant_embeddings = [info["embedding"] for info in mapping if info["chunk_id"] in chunk_id_to_text]
        else:
            return jsonify({"response": "Dữ liệu embedding không hợp lệ."}), 400

        if not relevant_embeddings:
            return jsonify({"response": "Không có embedding nào được tải."}), 404

        # Tính điểm tương tự
        query_embedding = get_embedding(query)
        phoBert_scores = np.dot(relevant_embeddings, query_embedding) 
        bm25_scores_selected = np.array([bm25_scores[i % len(bm25_scores)] for i in range(len(phoBert_scores))])
        combined_scores = 0.45 * bm25_scores_selected + 0.55 * phoBert_scores

        # Lấy các chunk tốt nhất
        top_25_idx = np.argsort(combined_scores)[::-1][:25]
        top_chunks = [(list(chunk_id_to_text.keys())[i], chunk_id_to_text[list(chunk_id_to_text.keys())[i]]) for i in top_25_idx]

        if top_chunks:
            prompt = create_prompt(chat_history, top_chunks, query)
            response = call_gpt_api(prompt)

            # Lưu lịch sử chat
            chat_history.append({"query": query, "response": response})
            if len(chat_history) > MAX_HISTORY_LENGTH:
                chat_history.pop(0)

            referenced_chunk_ids = re.findall(r"CHUNK_ID:\s*(\d+)", response)
            referenced_chunk_ids = list(map(int, referenced_chunk_ids)) 

            if referenced_chunk_ids:
                chunk_id_to_doc_id = {chunk[0]: chunk[1] for chunk in relevant_chunks}
                referenced_doc_ids = set(chunk_id_to_doc_id[chunk_id] for chunk_id in referenced_chunk_ids if chunk_id in chunk_id_to_doc_id)
                related_documents = [doc for doc in documents if doc.id in referenced_doc_ids]

                if related_documents:
                    related_info = [{"filename": doc.filename, "content": doc.content[:1200]} for doc in related_documents]
                    return jsonify({"response": response, "related_documents": related_info}), 200
                else:
                    return jsonify({"response": response, "related_documents": []}), 200
            else:
                return jsonify({"response": "Không tìm thấy `CHUNK_ID` trong câu trả lời của GPT."}), 404
        else:
            return jsonify({"response": "Không tìm thấy văn bản nào phù hợp."}), 404

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"response": "Đã xảy ra lỗi: " + str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)