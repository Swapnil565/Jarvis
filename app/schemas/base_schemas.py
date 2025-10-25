"""
Base schemas for JARVIS 3.0 Backend
Common Pydantic models and response structures
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BaseResponse(BaseModel):
    """Base response model"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseResponse):
    """Success response model"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Any] = None


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(ErrorResponse):
    """Validation error response model"""
    validation_errors: List[Dict[str, Any]] = []


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model"""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        limit: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response"""
        pages = (total + limit - 1) // limit
        return cls(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class SearchParams(BaseModel):
    """Search parameters"""
    query: str = Field(description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Results offset")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str
    message: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Optional[Dict[str, Any]] = None
    uptime_seconds: Optional[float] = None


class MetricsResponse(BaseModel):
    """Metrics response model"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    request_count: int
    response_time_avg: float
    error_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)


class FileUploadResponse(BaseModel):
    """File upload response model"""
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    upload_url: Optional[str] = None
    processing_status: str = "pending"


class BulkOperationResponse(BaseModel):
    """Bulk operation response model"""
    total_items: int
    successful_items: int
    failed_items: int
    errors: List[Dict[str, Any]] = []
    processing_time_ms: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API key response model"""
    key_id: str
    key_name: str
    masked_key: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class SystemConfigResponse(BaseModel):
    """System configuration response model"""
    app_name: str
    version: str
    environment: str
    features: Dict[str, bool]
    limits: Dict[str, int]
    maintenance_mode: bool = False