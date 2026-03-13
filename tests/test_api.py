import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
import json

client = TestClient(app)

@pytest.fixture
def mock_rag_response_success():
    return {
        "answer": "This is a test answer about subscription.",
        "can_answer": True,
        "sources": ["faq.md"],
        "confidence": 0.9,
        "create_support_ticket": False
    }

@pytest.fixture
def mock_rag_response_failure():
    return {
        "answer": "I cannot answer that question.",
        "can_answer": False,
        "sources": [],
        "confidence": 0.0,
        "create_support_ticket": True
    }

@pytest.fixture
def mock_ticket_result():
    return {
        "ticket_id": "12345",
        "created": True
    }
# Enpoint tests
class TestChatEndpoint:
    def test_chat_endpoint_success(self, mock_rag_response_success):
        with patch("app.api.routes.RAGGenerator.generate",
                    new_callable=AsyncMock, return_value=mock_rag_response_success), \
            patch("app.api.routes.ticket_service.create_ticket",new_callable=AsyncMock, return_value=None), \
            patch("app.api.routes.cache_service.set",new_callable=AsyncMock):
        
            response = client.post("/api/v1/chat",json={
                "message":"How cancel my subscription?",
                "user_email":"tes@ejemplo.com",
                "user_name": "Test User" 
            })
        
        assert response.status_code==200
        data= response.json()
        assert data["can_answer"] is True
        assert data["ticket_created"] is False
        assert "subscription" in data["response"].lower()
        assert data["ticket_id"] is None
        assert len(data["conversation_id"])>0

    def test_ticket_creation_on_unknown_query(
            self,
            mock_rag_response_failure,
            mock_ticket_result):
        
        with patch("app.api.routes.RAGGenerator.generate",
                    new_callable=AsyncMock, return_value=mock_rag_response_failure),\
            patch("app.api.routes.cache_service.get",new_callable=AsyncMock, return_value=None),\
            patch("app.api.routes.ticket_service.create_ticket",new_callable=AsyncMock, return_value=mock_ticket_result):
            
            response =client.post("/api/v1/chat",json={
                "message":"What is the meaning of life?",
                "user_email":"test@ejemplo.com",
                "user_name": "Test User" })
            
        assert response.status_code==200
        data = response.json()
        assert data["can_answer"] is False
        assert data["ticket_created"] is True
        assert data["ticket_id"] == "12345"

    def test_cache_hit(self, mock_rag_response_success):
        cached_data = {
            "response": "This is a test answer about subscription.",
            "can_answer": True,
            "sources": ["faq.md"],
            "confidence": 0.9,
            "conversation_id": "cached-conversation-id",
            "ticket_created": False,
            "ticket_id": None,
            "from_cache": True
        }
        
        with patch("app.api.routes.cache_service.get",new_callable=AsyncMock, return_value=cached_data) as mock_cahe,\
            patch("app.api.routes.RAGGenerator.generate",new_callable=AsyncMock) as mock_generetor:
                response = client.post("/api/v1/chat",json={
                    "message":"How cancel my subscription?",
                    "user_email":"test@ejemplo.com",
                    "user_name": "Test User" 
                })
        
        assert  response.status_code == 200
        assert response.json()["from_cache"] is True

        mock_generetor.assert_not_called()
    
    def test_validation_empty_message(self):
        response = client.post("/api/v1/chat",json={
            "message":"",
            "user_email":"test@example.com",
            "user_name": "Test User" })
        assert response.status_code == 422
    
    def test_validation_message_to_long(self):
        response =client.post("/api/v1/chat",json={
            "message":"a"*2001,
            "user_email":"test@ejemplo.com",
            "user_name": "Test User" })
        assert response.status_code == 422
    
    def test_conversation_id_preserved(self,mock_rag_response_success):
        with patch("app.api.routes.RAGGenerator.generate",new_callable = AsyncMock,return_value=mock_rag_response_success),\
            patch("app.api.routes.cache_service.get",new_callable=AsyncMock,return_value=None),\
            patch("app.api.routes.cache_service.set",new_callable=AsyncMock):

            response = client.post("/api/v1/chat", json={
                "message": "What plans are available?",
                "conversation_id": "idee1234",
                "user_email": "test@test.com",
                "user_name": "Test User"
            })
        assert response.json()["conversation_id"] == "idee1234"

# --Test endpoint---

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# --Test documentation
def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


