import logging
import os
import pickle
from flask import Flask, request, jsonify
from database.create_database import create_tables
from database.embedding import save_embeddings_to_pkl
from utils.utils import save_all_txt_in_folder, read_and_chunk_files_from_folder
from configs.settings import UPLOAD_FOLDER, EMBEDDINGS_PATH

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logger.error("Không tìm thấy file trong request.")
        return jsonify({"error": "Không tìm thấy file trong request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("Tên file không hợp lệ.")
        return jsonify({"error": "Tên file không hợp lệ"}), 400
    
    if not file.filename.endswith('.txt'):
        logger.error("Chỉ hỗ trợ file .txt.")
        return jsonify({"error": "Chỉ hỗ trợ file .txt"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    if os.path.exists(file_path):
        logger.error("File đã tồn tại: %s", file_path)
        return jsonify({"error": "File đã tồn tại"}), 400
    
    file.save(file_path)
    logger.info("Đã lưu file: %s", file_path)

    save_all_txt_in_folder()
    read_and_chunk_files_from_folder()
    save_embeddings_to_pkl()
    
    logger.info("Tải lên thành công: %s", file_path)
    return jsonify({"message": "Tải lên thành công!", "file_path": file_path}), 200

@app.route('/get_all_embeddings', methods=['GET'])
def get_all_embeddings():
    if not os.path.exists(EMBEDDINGS_PATH):
        logger.error("Không tìm thấy embeddings.")
        return jsonify({"error": "Không tìm thấy embeddings"}), 500
    
    with open(EMBEDDINGS_PATH, "rb") as f:
        embeddings = pickle.load(f)
    
    logger.info("Đã lấy tất cả embeddings thành công.")
    return jsonify(embeddings), 200

if __name__ == '__main__':
    logger.info("Khởi động ứng dụng...")
    create_tables()
    save_all_txt_in_folder()
    read_and_chunk_files_from_folder()
    save_embeddings_to_pkl()
    app.run(debug=True)