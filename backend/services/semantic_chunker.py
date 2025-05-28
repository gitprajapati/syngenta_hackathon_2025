#services/semantic_chunker.py
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import os
from typing import List
from services.customeEmbedingModel import ClientAPIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from core.config import settings
SYN_MODEL_API_KEY = os.getenv('SYN_MODEL_API_KEY')


def load_pdf_and_chunk(file) -> List[str]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    loader = PyPDFLoader(tmp_path)
    pages = loader.load()

    custom_embeddings = ClientAPIEmbeddings(api_key = settings.SYN_MODEL_API_KEY)
    

    full_text = "\n\n".join([page.page_content for page in pages])
    
    splitter = SemanticChunker(
        custom_embeddings,
        breakpoint_threshold_type="gradient",
        breakpoint_threshold_amount=95
        
    )
    chunks = splitter.split_text(full_text)

    os.remove(tmp_path)  
    
    return chunks
