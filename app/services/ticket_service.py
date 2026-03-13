"""Ticket service module
This module defines the TicketService class responsible for creating support tickets
when the agent cannot answer a user's query. It interacts with an external ticketing system API.

Support Api integration with:
- Surbase
- Zendesk
- HubSpot"""

import httpx
import logging
from app.core.config import get_settings
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)
settings = get_settings()

# Data model for support ticket creation result

class TicketData:
    """Data model for support ticket creation result"""
    def __init__(self, 
                 user_query: str,
                 user_email:str,
                 user_name:str,
                 conversation_id:str,
                 conversation_history:list,
                 metadata:dict):
        
        self.user_query = user_query
        self.user_email = user_email or "anonymous"
        self.user_name = user_name or "user"
        self.conversation_id = conversation_id
        self.conversation_history = conversation_history
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()

# Backend API client for support ticket system

class SupabaseTicketBackend:
    """Backend client for Supabase ticketing system"""
    def __init__(self):
        self.client: Client = create_client(
            settings.support_ticket_api_url, 
            settings.support_ticket_api_key.get_secret_value())
    
    async def create_ticket(self, ticket_data: TicketData) -> dict:
        """Create a support ticket in Supabase"""
        try:
            response = self.client.table("support_tickets").insert({
                "user_query": ticket_data.user_query,
                "user_email": ticket_data.user_email,
                "user_name": ticket_data.user_name,
                "conversation_id": ticket_data.conversation_id,
                "conversation_history": ticket_data.conversation_history,
                "metadata": ticket_data.metadata,
                "created_at": ticket_data.created_at,
                "status": "open"
            }).execute()
            
            ticket_id = None
            if response.data and isinstance(response.data[0], dict):
                ticket_id = response.data[0].get("id")
            logger.info(f"Support ticket created with ID: {ticket_id}")
            return {"ticket_id": ticket_id, "created": True}
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return {"ticket_id": None, "created": False}
        
class TicketService:
    """Service for handling support ticket creation"""
    def __init__(self):
        self.backend = SupabaseTicketBackend()
    
    async def create_ticket(self, 
                            user_query: str,
                            user_email:str,
                            user_name:str,
                            conversation_id:str,
                            conversation_history:list) -> dict:
        """Create a support ticket with the given user query and conversation context"""
        ticket_data = TicketData(
            user_query=user_query,
            user_email=user_email,
            user_name=user_name,
            conversation_id=conversation_id,
            conversation_history=conversation_history,
            metadata={}
        )
        return await self.backend.create_ticket(ticket_data)