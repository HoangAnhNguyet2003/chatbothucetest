from rank_bm25 import BM25Okapi

def get_bm25_retriever(documents):
    document_texts = [doc.content for doc in documents]
    tokenized_docs = [text.split() for text in document_texts]
    return BM25Okapi(tokenized_docs)

def retrieve_top_k(bm25, query, k=20):
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    top_k_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return top_k_idx, scores
