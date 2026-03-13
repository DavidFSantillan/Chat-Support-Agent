from openai import AsyncOpenAI
from app.core.config import get_settings
from app.rag.retriver import DocumentRetriver
import logging
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)
settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

# ---System prompt for the RAG model---
SYSTEM_PROMPT = """You are a helpful, polite and precise assistant for answering 
                questions about a company's products and services. 
                Follow the following guidelines when answering questions:
1. Use only the following retrieved documents to answer the question.
2. If the retrieved documents do not contain relevant information, say you don't know.
3. Be concise and to the point in your answers.
4. Do not use any information that is not in the retrieved documents.
5. Always cite the source of the information in the retrieved documents using the format [source: document_id].
6. If the question is not related to the company's products or services, say you don't know.
7. Use bullet points if you need to list multiple items in the answer.
8. At the end ask if the user needs more help or has any follow-up questions.
9. Always be polite and professional in your responses.
10. Responses should be in English unless the question is asked in another language, then respond in that language.
"""
CANNOT_ANSWER_PROMPT = """You are a helpful, polite and precise assistant for answering 
                questions about a company's products and services. 
                Follow the following guidelines when answering questions:
1. If the retrieved documents do not contain relevant information to answer the question, say you don't know.
2. Always be polite and professional in your responses.
3. Explain that you would create a ticket for the user's question and that a human agent will get back to them soon.
4. The time to get back to the user will depend on the support team's workload and the complexity of the issue, but they will try to get back to the user as soon as possible."""

class RAGGenerator:
    """Class to generate answers to user questions using retrieved 
    documents from Pinecone vector database and a language model"""

    def __init__(self):
        self.retriever = DocumentRetriver()
    def _buil_context(self,documents:list[dict]) -> str:
        """Build the context string for the language model prompt using the retrieved documents"""
        context_part = []

        for i, doc in enumerate(documents,1):
            context_part.append(
                f"-- Source {i}:{doc['source']} (relevance_score: {doc['score']})--\n{doc['text']}\n"
            )
        return "\n\n".join(context_part)
    async def generate(
            self,
            query: str,
            conversation_history: list[ChatCompletionMessageParam] | None = None) -> dict:
    
        """Generate an answer to the user question using retrieved documents and a language model"""
        if conversation_history is None:
            conversation_history = []
        
        # Retrieve
        can_answer, docs = await self.retriever.query_answer(query)
        # logger.info(f"First doc keys: {docs[0].keys()}")
        # logger.info(f"First doc text: {docs[0].get('text', 'EMPTY')[:200]}")
        if not can_answer:
            logger.info(f"RAG Generator cannot answer the question: {query} based on retrieved documents. Returning cannot answer prompt.")
            answer = await self._generate_cannot_answer_response(query)
            return {
                "answer": answer,
                "can_answer": False,
                "sources": [],
                "confidence": docs[0]["score"] if docs else 0.0,
                "create_support_ticket": True
            }
        # Build context
        context = self._buil_context(docs)
        # logger.info(f"CONTEXT BEING SENT TO GPT:\n{context}")
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        
        user_message: ChatCompletionMessageParam = {"role": "user", \
                                                    "content": f"RETRIEVED DOCUMENTS:\n{context}\n\nUSER QUESTION:\n{query}\n\nAnswer using ONLY the retrieved documents above."}
        messages.append(user_message)
        
        # Generate answer using language model
        logger.info(f"Generating answer for query: {query} using RAG model with context from retrieved documents.")
        response = await client.chat.completions.create(
            model=settings.rag_model_name,
            messages=messages,
            max_tokens=settings.rag_max_tokens,
            temperature=settings.rag_temperature,
        )
        answer = response.choices[0].message.content
        sources = list(set([doc["source"] for doc in docs]))
        logger.info(f"Generated answer for query: {query} using RAG model.")

        return {
            "answer": answer,
            "can_answer": True,
            "sources": sources,
            "confidence": docs[0]["score"] if docs else 0.0,
            "create_support_ticket": False
        }
    
    async def _generate_cannot_answer_response(self, query: str) -> str:
        """Generate a response to the user when the RAG model cannot answer the question based on retrieved documents"""
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": CANNOT_ANSWER_PROMPT},
            {"role": "user", "content": f"Question: {query}"}
        ]

        response = await client.chat.completions.create(
            model=settings.rag_model_name,
            messages=messages,
            max_tokens=settings.rag_max_tokens,
            temperature=settings.rag_temperature,
        )
        answer = response.choices[0].message.content or ""
        logger.info(f"Generated cannot answer response for query: {query} using RAG model.")
        return answer
    