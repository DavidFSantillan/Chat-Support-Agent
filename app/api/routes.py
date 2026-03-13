from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from app.rag.generator import RAGGenerator 
from app.services.cache_service import CacheService
from app.services.ticket_service import TicketService
import uuid
import logging

router = APIRouter()

logger = logging.getLogger(__name__)
router = APIRouter()

# Instances of services
cache_service = CacheService()
ticket_service = TicketService()
response_generator = RAGGenerator ()

# Schemas
class ChatRequest(BaseModel):
    """Schema for chat request
    """
    message: str = Field(..., min_length=1, max_length=2000, 
                         description="User's message to the support agent", 
                         example="I need help with my order.")
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                                 description="Unique identifier for the conversation")
    user_email: str = Field(..., description="User's email address",
                                 example="user@example.com")    
    user_name: str = Field(..., description="User's name",
                                 example="John Doe")
    conversation_history: list[dict] = Field(default_factory=list, 
                                             description="List of previous messages in the conversation")
    
    class Config:
        json_schema_extra = {
            "example": {  
                "message": "I need help with my order.",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_email": "user@example.com",
                "user_name": "John Doe",
            }
        }

class ChatResponse(BaseModel):
    """Schema for chat response
    """
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    response: str = Field(..., description="Support agent's response to the user's message")
    can_answer: bool = Field(..., description="Indicates if the agent can answer the user's question")
    ticket_id: str | None = Field(None, description="ID of the created support ticket, if applicable")
    sources: list[str] = Field(default_factory=list, description="List of sources used to generate the response")
    confidence: float = Field(..., description="Confidence score of the generated response")  
    from_cache: bool = Field(..., description="Indicates if the response was retrieved from cache")
    ticket_created: bool = Field(..., description="Indicates if a support ticket was created for this conversation")    
    class Config:
        json_schema_extra = {
            "example": {  
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "answer": "Sure, I can help you with that. Can you please provide your order number?",
                "can_answer": True,
                "ticket_id": None,
                "sources": ["knowledge_base_article_123", "previous_conversation_456"],
                "confidence": 0.95,
                "from_cache": False,
                "ticket_created": False
            }
        }

class HelthCheckResponse(BaseModel):
    """Schema for health check response
    """
    status: str = Field(..., description="Health status of the API", example="ok")  
    version: str = Field(..., description="API version", example="1.0.0")
    uptime: float = Field(..., description="API uptime in seconds", example=12345.67)

@router.post("/chat", response_model=ChatResponse,
             summary="Handle user messages and generate responses",
               description="Endpoint to handle incoming user messages, " \
               "generate responses using RAG, and manage support tickets.")

async def chat_endpoint(request: ChatRequest, 
                        background_tasks: BackgroundTasks):
    """Endpoint to handle incoming user messages, generate responses using RAG, and manage support tickets.
    """
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    logger.info(f"Received chat request for conversation_id: {conversation_id}")

    # Check cache for existing response
    cached_response = await cache_service.get(request.message)
    if cached_response:
        cached_response["conversation_id"] = conversation_id
        cached_response["from_cache"] = True
        return ChatResponse(**cached_response)
    # Generate response using RAG
    try:
        result = await response_generator.generate(
            query=request.message,
            conversation_history=request.conversation_history
        )
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=503, 
                            detail="Error generating response")
    
    # Create support ticket if agent cannot answer
    ticket_id = None
    ticket_created = False
    if not result["can_answer"]:
        logger.info(f"Agent cannot answer, creating support ticket for conversation_id: {conversation_id}")
        try:
            ticket_result = await ticket_service.create_ticket(
                user_query=request.message,
                user_email=request.user_email,
                user_name=request.user_name,
                conversation_id=conversation_id,
                conversation_history=request.conversation_history
            )
            ticket_id=ticket_result.get("ticket_id")
            ticket_created = ticket_result.get("created", False)
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            raise HTTPException(status_code=503, 
                                detail="Error creating support ticket")   
    # Asamble response with ticket information
    response_data = {
        "conversation_id": conversation_id,
        "response": result["answer"],
        "can_answer": result["can_answer"],  
        "ticket_id": ticket_id,
        "ticket_created": ticket_created,
        "sources": result["sources"],
        "confidence": result["confidence"],
        "from_cache": False
    }   
    
    # Cache the response for future requests
    if result["can_answer"]:
        background_tasks.add_task(cache_service.set, request.message, response_data)
    return ChatResponse(**response_data)

@router.get("/health", response_model=HelthCheckResponse,summary="Health check endpoint", description="Endpoint to check the health status of the API")
async def health_check():
    """Endpoint to check the health status of the API
    """
    from app.core.config import get_settings
    settings = get_settings()
    return HelthCheckResponse(status="ok", version=settings.app_version, uptime=12345.67)
@router.delete("/cache", summary="Clear cache", description="Endpoint to clear the response cache")
async def clear_cache():
    """Endpoint to clear the response cache
    """
    deleted = await cache_service.clear()
    return {"message": f"Cache cleared successfully, {deleted} items removed."} 
@router.get("/cache/stats", summary="Cache statistics", description="Endpoint to get cache statistics")
async def cache_stats():
    """Endpoint to get cache statistics
    """
    stats = await cache_service.get_stats()
    return stats