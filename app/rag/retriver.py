from pinecone import Pinecone
from app.core.config import get_settings
from app.rag.embeddings import get_embedding
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class DocumentRetriver:
    """Class to retrieve relevant documents from Pinecone 
    vector database based on query embeddings"""

    def __init__(self):
        pc = Pinecone(api_key=settings.pinecone_api_key.get_secret_value())
        self.index=pc.Index(settings.pinecone_index_name)
        
    async def retrieve(self, query: str, top_k: int = settings.rag_top_k) -> list[dict]:
        """Retrieve relevant documents from Pinecone based on query embeddings"""
        query_vector = await get_embedding(query)
        logger.info(f"Query embedding vector obtained for query: {query}")
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True)
        documents = []
        matches = results.matches
        for match in matches:
            documents.append({
                "id": match.id,
                "score": round(match.score,4),
                "metadata": match.metadata,
                "source": match.metadata.get("source", "unknown"),
                "text": match.metadata.get("text", "")
            })

        logger.info(f"Retrieved {len(documents)} documents from Pinecone for query: {query}")
        return documents
    
    async def query_answer(self, query: str) -> tuple[bool,list[dict]]:
        """Query Pinecone for relevant documents and return whether any relevant documents were found along with the retrieved documents"""
        documents = await self.retrieve(query)
        if len(documents) == 0:
            logger.info(f"No relevant documents found in Pinecone for query: {query}")
            return False, []
        else:
            best_score = documents[0]["score"]
            can_answer = best_score >= settings.rag_score_threshold
            logger.info(f"Best score among retrieved documents: {best_score} for query: {query}")
            
            return can_answer, documents