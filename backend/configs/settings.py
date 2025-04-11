import os

# OpenAI API Key
OPENAI_API_KEY = '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'

# FAISS mapping path
UPLOAD_FOLDER = './database/file_data'
EMBEDDINGS_PATH = './embeddings.pkl'

# Cấu hình database
DB_CONFIG = {
    "DRIVER": "SQL Server",
    "SERVER": "DESKTOP-CSDJ6DE\\SQLEXPRESS",
    "DATABASE": "chatbot",
    "USERNAME": "DESKTOP-CSDJ6DE\\sonvu", 
    "Trusted_Connection": "yes"
}
