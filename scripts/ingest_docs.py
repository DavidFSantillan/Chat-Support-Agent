"""ingest_docs.py: Ingest documents into the vector database.
This script reads documents from the specified directory, processes them using the DocumentProcessor,
and stores the resulting embeddings in the vector database. It also handles metadata extraction and logging.
Usage:
    python ingest_docs.py --docs_dir ./path_to_docs --chunk_size 500 --over"""

import argparse
import os
import logging 
import asyncio
from pathlib import Path
import sys
from typing import Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

import pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader
)
import dotenv
dotenv.load_dotenv()

Pinecone = getattr(pinecone, "Pinecone", None)
ServerlessSpec = getattr(pinecone, "ServerlessSpec", None)

from app.core.config import get_settings
from app.rag.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

# Loader fuction to determine the appropriate loader based on file type
def get_loader(file_path: Path) -> Optional[Any]:
    """Get the appropriate document loader based on file type"""
    suffix = file_path.suffix.lower()
    if suffix in [".txt", ".rst"]:
        return TextLoader(str(file_path),encoding="utf-8")  
    elif suffix == ".pdf":
        return PyPDFLoader(str(file_path))
    elif suffix  in [".docx", ".doc"]:
        return UnstructuredWordDocumentLoader(str(file_path))
    elif suffix in [".md", ".markdown"]:
        return UnstructuredMarkdownLoader(str(file_path))
    else:
        logger.warning(f"Unsupported file type: {file_path.suffix} for file {file_path.name}")
        return None
    
def chunk_documents(documents: list, chunk_size: int = 800, overlap:int=100) -> list:
    """Chunk documents into smaller pieces using RecursiveCharacterTextSplitter"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", "",". "],
        length_function=len
    )
    chunk=text_splitter.split_documents(documents)
    logger.info(f"Chunked {len(documents)} documents into {len(chunk)} chunks with chunk size {chunk_size} and overlap {overlap}")
    return chunk