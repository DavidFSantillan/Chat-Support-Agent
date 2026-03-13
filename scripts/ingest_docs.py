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
import time
from yaml import loader
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
sys.path.append(str(Path(__file__).parent.parent))
Pinecone = getattr(pinecone, "Pinecone", None)
ServerlessSpec = getattr(pinecone, "ServerlessSpec", None)

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings_batch

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
        return TextLoader(str(file_path), encoding="utf-8")
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

# Indexing function to process documents and store embeddings in Pinecone
async def ingest_doc(
        doc_dir:str="./data/docs",
        chunk_size:int=800,
        batch_size:int=100,
        recreate_index:bool=False):
    """Ingest documents into Pinecone vector database
    Pipeline:
        1. Load documents from the specified directory
        2. Chunk documents into smaller pieces
        3. Generate embeddings for each chunk using the embedding service
        4. Store embeddings in Pinecone vector database with metadata
    Args:
        doc_dir (str): Directory containing documents to ingest
        chunk_size (int): Size of each document chunk
        batch_size (int): Number of chunks to process in each batch
        recreate_index (bool): Whether to recreate the Pinecone index before ingestion
    """
    # Initialize Pinecone client
    pc=Pinecone(api_key=settings.pinecone_api_key.get_secret_value())
    # Create or recreate Pinecone index
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if settings.pinecone_index_name not in existing_indexes:
        logger.info(f"Creating Pinecone index: {settings.pinecone_index_name}")
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.pinecone_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        logger.info(f"Index {settings.pinecone_index_name} created successfully")
        time.sleep(10)  # Wait for index to be ready
    elif recreate_index:
        logger.info(f"Recreating Pinecone index: {settings.pinecone_index_name}")
        pc.delete_index(name=settings.pinecone_index_name)
        time.sleep(5)  # Wait for index deletion
        await ingest_doc(doc_dir=doc_dir, chunk_size=chunk_size, batch_size=batch_size, recreate_index=False)
        return

    index=pc.Index(settings.pinecone_index_name)
    # ---Load documents from the specified directory---
    docs_path =Path(doc_dir)
    all_docs = []

    for pattern in ["*.txt", "*.pdf", "*.docx", "*.doc", "*.md", "*.markdown"]:
        for file_path in docs_path.rglob(pattern):
            loader = get_loader(file_path)
            if loader is None:
                continue
            documents = loader.load()
            if documents is not None:
                try:
                    for doc in documents:
                        doc.metadata["source"] = str(file_path)
                    all_docs.extend(documents)
                    logger.info(f"Loaded {len(all_docs)} documents from {file_path.name}")
                except Exception as e:
                    logger.error(f"Error loading {file_path.name}: {e}")

    # #---Chunk documents into smaller pieces---
    chunks=chunk_documents(all_docs, chunk_size=chunk_size)
    # ---Generate embeddings for each chunk and store in Pinecone---
    total_indexed = 0
    for i in range(0, len(chunks), batch_size):

        batch_chunks = chunks[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches}: {len(batch_chunks)} chunks")
        
        texts = [chunk.page_content for chunk in batch_chunks]
        metadatas = [chunk.metadata for chunk in batch_chunks]

        try:
            embeddings = await get_embeddings_batch(texts)

            vectors = []
            for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                chunk_id = f"{chunk.metadata['source']}_{j}"
                vectors.append({
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": {
                        "source": chunk.metadata["source"],
                        "page": chunk.metadata.get("page", 0),
                        "chunk_index":i+j,
                        "text_length": len(chunk.page_content),
                        "text": chunk.page_content
                    }})
            index.upsert(vectors=vectors)
            total_indexed += len(vectors)
            logger.info(f"Indexed {len(vectors)} chunks in batch {batch_num}/{total_batches}. Total indexed: {total_indexed}")
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}/{total_batches}: {e}")
        
        logger.info(f"Finished processing batch {batch_num}/{total_batches}")

        stats=index.describe_index_stats()
        logger.info(f"Current index stats: {stats}")

# --- Main entry point for script execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into Pinecone vector database")
    parser.add_argument("--docs_dir", type=str, default="./data/docs", 
                        help="Directory containing documents to ingest")
    parser.add_argument("--chunk_size", type=int, default=800, 
                        help="Size of each document chunk")
    parser.add_argument("--batch_size", type=int, default=100, 
                        help="Number of chunks to process in each batch")
    parser.add_argument("--recreate_index", action="store_true", 
                        help="Whether to recreate the Pinecone index before ingestion")
    args = parser.parse_args()

    asyncio.run(ingest_doc( 
        doc_dir=args.docs_dir,
        chunk_size=args.chunk_size,
        batch_size=args.batch_size,
        recreate_index=args.recreate_index
    ))