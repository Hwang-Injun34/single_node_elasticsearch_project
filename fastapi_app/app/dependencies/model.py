from fastapi import Depends 
from kiwipiepy import Kiwi
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer 

from app.core.state import state 

# 헬퍼 함수(None 체크)
def _get_state_item(key: str, error_msg: str):
    item = state.get(key)
    if item is None:
        raise RuntimeError(error_msg)
    return item

def get_embedding_model() -> SentenceTransformer:
    return _get_state_item("embedding_model", "Embedding model is not initialized.")


def get_kiwi_instance() -> Kiwi:
    return _get_state_item("kiwi_instance", "Kiwi instance is not initialized.")

def get_keybert_model() -> KeyBERT:
    return _get_state_item("keybert_model", "KeyBERT model is not initialized.")
