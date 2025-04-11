import os
import pickle
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from configs.settings import EMBEDDINGS_PATH

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load PhoBERT model
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base").to(device)

def load_faiss_mapping():
    if not os.path.exists(EMBEDDINGS_PATH):
        return None
    try:
        with open(EMBEDDINGS_PATH, "rb") as f:
            mapping = pickle.load(f)
        return mapping
    except Exception as e:
        print(f"Lỗi khi tải FAISS mapping: {e}")
        return None

def get_embedding(text):
    tokens = tokenizer(text, padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
    with torch.no_grad():
        embedding = torch.mean(model(**tokens).last_hidden_state, dim=1).squeeze(0).cpu().numpy()
    return embedding / np.linalg.norm(embedding)
