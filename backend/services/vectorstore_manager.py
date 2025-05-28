#services/vectorstore_manager.py
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from services.customeEmbedingModel import ClientAPIEmbeddings
import os, pickle
from uuid import uuid4
from core.config import settings
from services.topic_extractor import extract_topics_from_text

VECTOR_STORE_PATH =  settings.VECTOR_STORE_PATH
METADATA_PATH = settings.METADATA_PATH
embedding = ClientAPIEmbeddings(api_key=settings.SYN_MODEL_API_KEY)
if os.path.exists(VECTOR_STORE_PATH):
    vectorstore = FAISS.load_local(VECTOR_STORE_PATH, embedding, allow_dangerous_deserialization=True)
else:
    vectorstore = None

if os.path.exists(METADATA_PATH):
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
else:
    metadata = {} 


def save_vectorstore():
    vectorstore.save_local(VECTOR_STORE_PATH)
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)

def add_document(doc_id: str, file_name: str, chunks: list[str]):
    global vectorstore

    ids = [str(uuid4()) for _ in chunks]
    metadatas = [{"doc_id": doc_id, "file_name": file_name}] * len(chunks)

    if vectorstore is None:
        vectorstore = FAISS.from_texts(chunks, embedding=embedding, metadatas=metadatas, ids=ids)
    else:
        vectorstore.add_texts(chunks, ids=ids, metadatas=metadatas)

    full_text = "\n".join(chunks)
    extracted_topics = extract_topics_from_text(full_text)
    print(extracted_topics)
    metadata[doc_id] = {
        "file_name": file_name,
        "vector_ids": ids,
        "topics": extracted_topics  
    }

    save_vectorstore()
    return {
        "status": "added",
        "chunks": len(chunks),
        "doc_id": doc_id,
        "file_name": file_name,
        "topics": extracted_topics
    }


def delete_document(doc_id: str):
    if doc_id not in metadata:
        return {"status": "not_found", "doc_id": doc_id}
    try:
        vectorstore.delete(ids=metadata[doc_id]["vector_ids"])
    except Exception as e:
        print(f"Warning: failed to delete some vectors for {doc_id}: {e}")
    del metadata[doc_id]
    save_vectorstore()
    return {"status": "deleted", "doc_id": doc_id}


def get_all_documents():
    return [{"doc_id": doc_id, "file_name": meta["file_name"], "chunks": len(meta["vector_ids"]), "topics": meta["topics"]} for doc_id, meta in metadata.items()]


def get_all_topics() -> list[str]:
    all_topics = []
    for doc_meta in metadata.values():
        topics = doc_meta.get("topics", [])
        all_topics.extend(topics)
    return list(set(all_topics))

    