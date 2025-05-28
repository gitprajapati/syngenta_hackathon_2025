#routers/user.py
from fastapi import UploadFile, File, Form, APIRouter, HTTPException
from services.semantic_chunker import load_pdf_and_chunk
from services.vectorstore_manager import add_document, delete_document, get_all_documents
from uuid import uuid4
import os, pickle
from core.config import settings
from typing import List

VECTOR_STORE_PATH =  settings.VECTOR_STORE_PATH
METADATA_PATH = settings.METADATA_PATH

router = APIRouter(prefix="/doc", tags=["User can process documents here."])

# Load or initialize metadata
if os.path.exists(METADATA_PATH):
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
else:
    metadata = {}  

@router.post("/upload-multiple")
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    responses = []

    for file in files:
        for _, meta in metadata.items():
            if file.filename.lower() == meta["file_name"].lower():
                responses.append({
                    "file_name": file.filename,
                    "status": "duplicate"
                })
                break
        else:
            doc_id = str(uuid4())
            chunks = load_pdf_and_chunk(file)
            add_result = add_document(doc_id, file.filename, chunks)
            responses.append(add_result)

    return responses



@router.delete("/delete/{doc_id}")
async def delete_document_by_id(doc_id: str):
    return delete_document(doc_id)


@router.get("/all")
async def list_all_documents():
    return get_all_documents()
