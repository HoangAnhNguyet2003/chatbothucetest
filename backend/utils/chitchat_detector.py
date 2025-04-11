from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.preprocessing import normalize

class ChitChatDetector:
    def __init__(self):
    
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        self.model = AutoModel.from_pretrained("vinai/phobert-base")

        self.chitchat_examples = [
            "Bạn khỏe không?", "Chào bạn", "Cảm ơn bạn", "Tạm biệt", "Chúc bạn một ngày tốt lành",
            "Hi", "Hello", "Bạn là ai?", "Cảm ơn", "Xin chào", "Chào", "em chào thầy ạ", "em chào cô ạ", "e chào thầy/cô", "hi", "hello"
        ]

        self.chitchat_embeddings = self.encode_sentences(self.chitchat_examples)
        
    def encode_sentences(self, sentences):
      
        inputs = self.tokenizer(sentences, padding=True, truncation=True, return_tensors="pt", max_length=256)

        with torch.no_grad():
            outputs = self.model(**inputs)
            hidden_states = outputs.last_hidden_state 

            attention_mask = inputs["attention_mask"].unsqueeze(-1)
            embeddings = (hidden_states * attention_mask).sum(dim=1) / attention_mask.sum(dim=1)

        return normalize(embeddings.detach().cpu().numpy()) 

    def is_chitchat(self, query: str) -> bool:
        query_embedding = self.encode_sentences([query])[0] 
        cosine_scores = self.compute_cosine_similarity(query_embedding, self.chitchat_embeddings)
        return cosine_scores.max() > 0.8
    def compute_cosine_similarity(self, query_embedding, chitchat_embeddings):
        return np.dot(chitchat_embeddings, query_embedding) 
