"""
Pydantic schemas for JARVIS 3.0 Backend
API request/response models and validation schemas
"""

# Import all schemas to make them available at package level
from .base_schemas import *
from .query_schemas import *
# from .user_schemas import *
# from .document_schemas import *
# from .conversation_schemas import *
# from .auth_schemas import *

__all__ = [
    # Base schemas
    "BaseResponse",
    "ErrorResponse", 
    "SuccessResponse",
    "PaginatedResponse",
    "HealthCheckResponse",
    "SearchParams",
    "ValidationErrorResponse",
    "PaginationParams",
    "MetricsResponse",
    
    # Query schemas
    "QueryRequest",
    "QueryResponse",
    "SearchRequest", 
    "SearchResult",
    
    # User schemas (when implemented)
    # "UserCreate",
    # "UserUpdate", 
    # "UserResponse",
    # "UserLogin",
    # "UserProfile",
    
    # Auth schemas (when implemented)
    # "Token",
    # "TokenData",
    # "LoginRequest",
    # "RefreshTokenRequest",
    
    # Document schemas (when implemented)
    # "DocumentCreate",
    # "DocumentUpdate",
    # "DocumentResponse", 
    # "DocumentUpload",
    # "DocumentSearch",
    # "DocumentSearchResult",
    
    # Conversation schemas (when implemented)
    # "ConversationCreate",
    # "ConversationUpdate",
    # "ConversationResponse",
    # "MessageCreate", 
    # "MessageResponse",
    # "ChatRequest",
    # "ChatResponse"
]